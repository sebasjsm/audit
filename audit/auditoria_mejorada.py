# auditoria_mejorada.py
# Ejecutable por consola. Puede generar JSON local (--json)
# y/o empujar los datos al servidor FastAPI vía /link/push (con un CÓDIGO).

import json
import sys
import os
import getpass
import re
import subprocess
import psutil


OFFICE_DETECTADO_OPCION1 = None

def _detectar_tipos_discos():
    """
    Usa PowerShell (Get-PhysicalDisk) para obtener tipo real.
    Devuelve dict {FriendlyName: 'SSD'/'HDD'}.
    """
    tipos = {}
    try:
        cmd = (
            'powershell "Get-PhysicalDisk | '
            'Select FriendlyName, MediaType, BusType | '
            'Format-Table -HideTableHeaders"'
        )
        result = subprocess.check_output(cmd, shell=True).decode(errors="ignore").splitlines()

        for line in result:
            parts = line.strip().split()
            if not parts:
                continue

            name = parts[0]
            resto = " ".join(parts[1:]).upper()

            if "SSD" in resto:
                tipos[name] = "SSD"
            elif "HDD" in resto:
                tipos[name] = "HDD"
            else:
                tipos[name] = "HDD"  # fallback
    except Exception as e:
        print("Error detectando discos:", e)

    return tipos


def get_disk_capacities():
    """
    Lista capacidades aproximadas + tipo de disco.
    Ejemplo: ['500 GB SSD (NVMe)'].
    """
    discos = []
    tipos = _detectar_tipos_discos()

    try:
        for disk in psutil.disk_partitions(all=False):
            try:
                uso = psutil.disk_usage(disk.mountpoint)
                gb = round(uso.total / (1024**3))
                aprox = aproximar_capacidad(gb)

                cap = f"{aprox} GB" if aprox < 1000 else f"{int(aprox/1000)} TB"

                tipo = "HDD"
                for dev_id, kind in tipos.items():
                    if "C:" in disk.device.upper():  # emparejamos con C:
                        tipo = kind
                        break

                discos.append(f"{cap} {tipo}")

            except PermissionError:
                continue
    except Exception:
        return []

    return list(dict.fromkeys(discos))


# ... (lo demás igual)

def salir_rapido(code: int = 0):
    # Intenta vaciar buffers de consola y sale *inmediato*
    try:
        sys.stdout.flush()
        sys.stderr.flush()
    except Exception:
        pass
    os._exit(code)  # mata el proceso sin ejecutar atexit ni finalizers



MEM_CAPACIDADES_GB = [2, 3, 4, 5, 6, 8, 12, 16, 20, 24, 28, 32, 64]

def _parse_mem_to_float_gb(val) -> float:
    """
    Extrae número como float desde '19.83 GB', '31.7', 8, etc.
    """
    s = str(val or "").strip()
    num = ""
    for ch in s:
        if ch.isdigit() or ch == ".":
            num += ch
        elif num:
            break
    try:
        return float(num) if num else 0.0
    except Exception:
        return 0.0

def _normalizar_memoria_dropdown(val) -> str:
    """
    Mapea al valor **más cercano** de MEM_CAPACIDADES_GB.
    En caso de empate (p.ej. 22.0 entre 20 y 24), elige **hacia arriba**.
    """
    gb = _parse_mem_to_float_gb(val)   # ← usamos float, no int redondeado
    if gb <= 0:
        return ""
    canon = min(MEM_CAPACIDADES_GB, key=lambda x: (abs(x - gb), -x))  # tie->arriba
    return f"{int(canon)} GB"


# Tabla real de builds de Microsoft Office → año
OFFICE_BUILDS = [
    ("2007", 12,      0),
    ("2010", 14,      0),
    ("2013", 15,      0),
    ("2016", 16,   4266),
    ("2019", 16,  10336),
    ("2021", 16,  14332),
    ("2024", 16,  14931),   # LTSC 2024
]

def _leer_office_clicktorun():
    """Lee claves ClickToRun para detectar Office cuando no aparece en Uninstall."""
    if not winreg:
        return None
    rutas = [
        r"SOFTWARE\Microsoft\Office\ClickToRun\Configuration",
        r"SOFTWARE\Microsoft\Office\16.0\ClickToRun\Configuration",
    ]
    for hive in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
        for ruta in rutas:
            try:
                with winreg.OpenKey(hive, ruta) as k:
                    # valores útiles (algunos existen, otros no, según build)
                    ids = ""
                    ver = ""
                    for valname in ("ProductReleaseIds", "AudienceData"):
                        try:
                            ids = ids or str(winreg.QueryValueEx(k, valname)[0])
                        except FileNotFoundError:
                            pass
                    for valname in ("VersionToReport", "ClientVersionToReport"):
                        try:
                            ver = ver or str(winreg.QueryValueEx(k, valname)[0])
                        except FileNotFoundError:
                            pass
                    if ids or ver:
                        return {"ids": ids, "version": ver}
            except FileNotFoundError:
                continue
    return None


def _resolver_por_build(version_str):
    """
    Recibe algo como: 16.0.10396.20002
    Devuelve el año exacto según la tabla OFFICE_BUILDS.
    """
    if not version_str:
        return ""

    tokens = version_str.split(".")
    if len(tokens) < 3:
        return ""

    try:
        mayor = int(tokens[0])      # 16
        build = int(tokens[2])      # 10396
    except:
        return ""

    candidatos = []
    for year, req_major, req_build in OFFICE_BUILDS:
        if mayor == req_major and build >= req_build:
            candidatos.append((req_build, year))

    if not candidatos:
        return ""

    candidatos.sort(reverse=True)
    return candidatos[0][1]


def _canonicalizar_office(nombre: str, version: str) -> str:
    """
    Normalización básica cuando no hay datos suficientes.
    """
    low = (nombre or "").lower()

    # Libre / Open Office
    if "libreoffice" in low or "libre office" in low:
        return "LIBRE OFFICE"

    if "openoffice" in low or "open office" in low:
        m = re.search(r'(\d+(?:\.\d+)*)', nombre or "")
        return f"OPEN OFFICE {m.group(1)}" if m else "OPEN OFFICE"

    # Intento por año en DisplayName
    m = re.search(r'20(07|10|13|16|19|21|24)', low)
    if m:
        return f"OFFICE {m.group(0)}"

    # Intento por "versión mayor"
    mayor = (version or "").split(".")[0]
    mapa = {"12": "2007", "14": "2010", "15": "2013", "16": "2019"}
    if mayor in mapa:
        return f"OFFICE {mapa[mayor]}"

    return "OFFICE"


def _canon_office_por_releaseids(ids: str, version: str) -> str:
    """
    Normalización cuando Office es ClickToRun y solo tenemos ProductReleaseIds.
    """
    s = (ids or "").lower()

    # C2R/365 → tu catálogo lo marca como "2022"
    if any(k in s for k in ["o365", "office365", "microsoft 365", "businessretail", "homeprem"]):
        return "OFFICE 2022"

    # Office 2021 LTSC → lo mapeas también a 2022
    if ("2021" in s) or ("21" in s and "ltsc" in s):
        return "OFFICE 2022"

    if "2019" in s:
        return "OFFICE 2019"

    if "2016" in s:
        return "OFFICE 2016"

    # Intento por resolver build
    exact = _resolver_por_build(version)
    if exact:
        return f"OFFICE {exact}"

    return _canonicalizar_office(ids or "", version or "")


def detectar_office_y_version():
    """
    Detección de Office 100% confiable:
    1) Primero Uninstall (DisplayName)
    2) Luego ClickToRun si Uninstall no sirve
    3) Nunca usar build para determinar 2019/2021/2024 en MSI clásico
    """

    # ----------- 1) Buscar Office en Uninstall -----------
    for nombre, ver in _programas_instalados():

        low = nombre.lower()

        if "microsoft office" in low:
            # 🔹 Usamos el normalizador genérico
            canon = _canonicalizar_office(nombre, ver)
            return {
                "nombre": canon,
                "version": ver,
                "raw_name": nombre
            }

        # LibreOffice
        if "libreoffice" in low:
            return {"nombre": "LIBRE OFFICE", "version": ver, "raw_name": nombre}

    # ----------- 2) Fallback: ClickToRun -----------
    c2r = _leer_office_clicktorun()
    if c2r:
        ids = (c2r.get("ids") or "")
        ver = c2r.get("version") or ""

        # Aquí usamos el normalizador avanzado para C2R / 365 / LTSC
        canon = _canon_office_por_releaseids(ids, ver)  # ej. 'OFFICE 2021'

        return {
            "nombre": canon,
            "version": ver,
            "raw_name": ids
        }

    # ----------- 3) No se encontró nada -----------
    return {"nombre": "", "version": "", "raw_name": ""}

# Lista de capacidades estándar (ajústala a lo que tienes en tu sistema)
CAPACIDADES_ESTANDAR = [
    128, 220, 250, 256, 320, 500, 520, 720, 1000, 2000
]

def aproximar_capacidad(gb: int) -> int:
    """Devuelve la capacidad estándar más cercana a un valor en GB."""
    return min(CAPACIDADES_ESTANDAR, key=lambda x: abs(x - gb))


def _usuario_dominio() -> str:
    """Devuelve 'DOMINIO\\usuario' (o sólo usuario si no hay dominio)."""
    try:
        user = getpass.getuser() or os.environ.get("USERNAME", "")
    except Exception:
        user = os.environ.get("USERNAME", "")
    dom = os.environ.get("USERDOMAIN") or os.environ.get("COMPUTERNAME") or ""
    return f"{dom}\\{user}" if dom and user else (user or "")


# --- detectar antivirus y versión desde el registro de Windows ---
try:
    import winreg  # disponible en Windows
except Exception:
    winreg = None

_CANDIDATOS_AV = [
    "defender", "microsoft defender", "eset", "kaspersky", "norton",
    "mcafee", "bitdefender", "avast", "avg", "trend micro", "sophos", "panda"
]

def _programas_instalados():
    if not winreg:
        return []
    rutas = [
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
        r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall",
    ]
    hives = [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]
    encontrados = []
    for hive in hives:
        for ruta in rutas:
            try:
                with winreg.OpenKey(hive, ruta) as k:
                    subkeys = winreg.QueryInfoKey(k)[0]
                    for i in range(subkeys):
                        try:
                            sub = winreg.EnumKey(k, i)
                            with winreg.OpenKey(k, sub) as sk:
                                nombre = ""
                                version = ""
                                try:
                                    nombre = winreg.QueryValueEx(sk, "DisplayName")[0]
                                except FileNotFoundError:
                                    pass
                                try:
                                    version = winreg.QueryValueEx(sk, "DisplayVersion")[0]
                                except FileNotFoundError:
                                    pass
                                if nombre:
                                    encontrados.append((nombre, version))
                        except OSError:
                            continue
            except FileNotFoundError:
                continue
    return encontrados

def detectar_antivirus_y_version():
    """Devuelve dict {'nombre': str, 'version': str} o vacío si no encuentra."""
    mejor = {"nombre": "", "version": ""}
    for nombre, ver in _programas_instalados():
        low = nombre.lower()
        if any(pat in low for pat in _CANDIDATOS_AV):
            # prioriza el nombre más largo (suele ser el producto “real”)
            if len(nombre) > len(mejor["nombre"]):
                mejor = {"nombre": nombre, "version": ver or ""}
    return mejor



from pathlib import Path

def _ruta_json_salida() -> Path:
    """
    Devuelve la ruta donde se guardará datos_equipo.json.
    - Si está congelado (PyInstaller), guarda junto al .exe
    - Si corre como .py, guarda junto a este archivo
    """
    try:
        base = Path(sys.executable).parent  # cuando es .exe
    except Exception:
        base = Path(__file__).parent        # cuando es .py
    return base / "datos_equipo.json"



from aplicaciones import verificar_aplicaciones
from pc_info import (
    get_hostname, get_computer_type, get_computer_brand, get_computer_model,
    get_serial_number, get_computer_os, get_computer_architecture,
    get_computer_processor, get_computer_storage, get_total_memory,
    get_ip_address, is_dhcp_enabled
)
from limpieza import limpiar_todo

# ------------------ Utilidades ------------------

def _detectar_office() -> str:
    """Devuelve el nombre de Office si se detecta, si no cadena vacía."""
    candidatos = ["microsoft 365", "office", "libreoffice"]
    for nombre in candidatos:
        try:
            if verificar_aplicaciones(nombre):
                return nombre.title()
        except Exception:
            pass
    return ""

def _detectar_antivirus() -> str:
    """Devuelve el antivirus si se detecta, si no cadena vacía."""
    candidatos = [
        "defender", "eset", "kaspersky", "avast", "avg",
        "bitdefender", "norton", "mcafee", "trend micro",
    ]
    for nombre in candidatos:
        try:
            if verificar_aplicaciones(nombre):
                return nombre.title()
        except Exception:
            pass
    return ""

def _parse_mem_to_int_gb(val) -> int:
    """
    Convierte '31.78 GB' o '32' o 31.78 a entero en GB (≈).
    Si falla, devuelve 0.
    """
    try:
        s = str(val or "").strip()
        # toma el primer token numérico
        num = ""
        for ch in s:
            if ch.isdigit() or ch == ".":
                num += ch
            elif num:
                break
        if not num:
            return 0
        return int(round(float(num)))
    except Exception:
        return 0



def _auto_borrar(path: str, delay: int = 60):
    """
    Lanza un proceso independiente que, tras 'delay' segundos, borra 'path' si existe.
    Funciona aunque cierres el CMD con la X.
    """
    try:
        import subprocess, sys, os
        # Script inline que espera y borra
        script = (
            "import time, os; "
            f"time.sleep({delay}); "
            f"p=r'''{path}'''; "
            "os.remove(p) if os.path.exists(p) else None"
        )
        DETACHED_PROCESS = 0x00000008
        CREATE_NEW_PROCESS_GROUP = 0x00000200
        subprocess.Popen(
            [sys.executable, "-c", script],
            creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP,
            close_fds=True
        )
    except Exception:
        pass



# ------------------ Datos del equipo ------------------

def obtener_datos_equipo():
    """Obtiene todos los datos del equipo y los devuelve como diccionario (crudo)."""
    global OFFICE_DETECTADO_OPCION1

    ant = detectar_antivirus_y_version()

    # Si opción 1 ya detectó Office, usar ese mismo valor
    if OFFICE_DETECTADO_OPCION1:
        off = OFFICE_DETECTADO_OPCION1
    else:
        off = detectar_office_y_version()

    # Memoria normalizada
    _mem_raw = get_total_memory()
    _mem_norm = _normalizar_memoria_dropdown(_mem_raw)

    datos = {
        'hostname': get_hostname(),
        'computer_type': get_computer_type(),
        'computer_brand': get_computer_brand(),
        'computer_model': get_computer_model(),
        'serial_number': get_serial_number(),
        'computer_os': get_computer_os(),
        'computer_architecture': get_computer_architecture(),
        'computer_processor': get_computer_processor(),
        'computer_storage': get_computer_storage(),
        'computer_memory': _mem_norm,
        'disk_capacities': ", ".join(get_disk_capacities()),
        'ip_address': get_ip_address(),
        'usuarioDominio': _usuario_dominio(),
        'dhcp_info': is_dhcp_enabled(),

        # Office
        'office': off.get('nombre', ''),
        'office_version': off.get('version', ''),
        'office_raw_name': off.get('raw_name', ''),

        # Antivirus
        'antivirus': ant.get('nombre', ''),
        'antivirus_version': ant.get('version', '')
    }

    return datos

def guardar_json(datos, ruta_archivo):
    """Guarda los datos en un archivo JSON."""
    with open(ruta_archivo, 'w', encoding='utf-8') as f:
        json.dump(datos, f, indent=2, ensure_ascii=False)

# ------------------ Main / Menú ------------------

def main():
    # Modo automático: genera JSON y sale
    if len(sys.argv) > 1 and sys.argv[1] == '--json':
        datos = obtener_datos_equipo()
        guardar_json(datos, 'datos_equipo.json')
        print("Datos guardados en datos_equipo.json")
        return

    # Menú interactivo
    while True:
        print("---Inicio de la auditoria---")
        print("1. Verificar aplicaciones")
        print("2. Datos del equipo")
        print("3. Obtener dirección IP local")
        print("4. Hostname del equipo")
        print("5. Limpieza(temp y papelera)")
        print("6. Generar JSON con datos")
        print("9. Salir")

        try:
            opcion = input("Selecciona una opcion: ").strip()

            if opcion == '1':
                global OFFICE_DETECTADO_OPCION1

                filtro = input("Ingrese filtro de aplicación (Enter para todas): ")

                encontrado = verificar_aplicaciones(filtro)

                # detectar office REAL (siempre desde cero)
                off = detectar_office_y_version()

                # si el filtro incluye "office", guardamos la detección
                if "office" in filtro.lower():
                    # Detectar Office REAL, no solo el nombre del programa
                    detected_real = detectar_office_y_version()

                    if detected_real != "NO OFFICE DETECTADO":
                        OFFICE_DETECTADO_OPCION1 = detected_real
                    else:
                        OFFICE_DETECTADO_OPCION1 = off


                if not encontrado:
                    print("No se encontraron aplicaciones con ese filtro.")
                else:
                    print(f"Office detectado (opción 1): {off['nombre']} - {off['version']}")

            elif opcion == '2':
                print("Obteniendo datos de equipo...")
                datos = obtener_datos_equipo()
                print("###########################")
                for clave, valor in datos.items():
                    print(f"{clave}: {valor}")
                print("###########################")

                # Guardar JSON automáticamente junto al EXE
                salida = _ruta_json_salida()
                guardar_json(datos, salida)
                print(f"Datos guardados en: {salida}")



            elif opcion == '3':
                ip = get_ip_address()
                dhcp = is_dhcp_enabled()
                print(f"Dirección IP: {ip}")
                print(f"Configuración: {dhcp}")

            elif opcion == '4':
                hostname = get_hostname()
                print(f"Hostname: {hostname}")

            elif opcion == '5':
                confirmar = input("¿Está seguro de realizar limpieza? (s/n): ")
                if confirmar.lower() == 's':
                    limpiar_todo()
                else:
                    print("Limpieza cancelada.")

            elif opcion == '6':
                datos = obtener_datos_equipo()
                guardar_json(datos, 'datos_equipo.json')
                print("Datos guardados en datos_equipo.json")

            elif opcion == '9':
                print("Saliendo...", flush=True)
                os._exit(0)  # mata el proceso al instante


            else:
                print("Opción no válida.")

        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
