import socket
import subprocess
import platform
import shutil
import psutil


# ===============================
# Función para obtener la dirección IP local del equipo
# ===============================
def get_ip_address():
    try:
        # Crea un socket UDP (SOCK_DGRAM) usando IPv4 (AF_INET)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Conecta el socket a un servidor DNS público (Google 8.8.8.8, puerto 80)
        # No se envía ningún dato, solo se usa para que el sistema determine la IP local de salida
        s.connect(("8.8.8.8", 80))
        # Obtiene la dirección IP local asociada a la interfaz que se usaría para salir a Internet
        # getsockname() devuelve una tupla (ip, puerto), [0] toma solo la IP
        ip = s.getsockname()[0]
        # Cierra el socket para liberar recursos
        s.close()
        return ip
    except Exception as e:
        # Si ocurre un error, lo muestra en pantalla
        print("Error al obtener la dirección IP:", e)
        return None

# Muestra la IP local obtenida
#print("Tu dirección IP local es:", get_ip_address())

# ===============================
# Función para saber si la IP es asignada por DHCP o es manual (estática)
# ===============================
def is_dhcp_enabled():
    ip_obj = get_ip_address()
    ip_found = False
    dhcp_found = False
    try:
        # Ejecuta el comando 'ipconfig /all' y captura la salida en texto
        # encoding='latin-1' se usa para evitar errores de decodificación en Windows en español
        resultado = subprocess.run(["ipconfig", "/all"], capture_output=True, text=True, encoding="latin-1")
        salida = resultado.stdout.lower()  # Convierte toda la salida a minúsculas para facilitar la búsqueda
        # Recorre cada línea de la salida buscando la línea que indica si DHCP está habilitado
        for linea in salida.splitlines():
            if ip_obj in linea:
                ip_found = True
                if ip_found == True:
                    if dhcp_found == True:
                        mensaje = f"La IP {ip_obj} está asignada por DHCP (automática)."
                        return mensaje
                    elif dhcp_found == False:
                        mensaje = f"La IP {ip_obj} es manual (estática)."
                        return mensaje
                    return mensaje
                break
            if "dhcp habilitado" in linea or "dhcp enabled" in linea:
                # Si encuentra la línea, revisa si dice 'sí' o 'yes' (DHCP activado)
                if ": s¡" in linea or ": yes" in linea or ": sí" in linea:
                    #print(f"La IP está asignada por DHCP (automática).")
                    dhcp_found = True
                # Si dice 'no', la IP es manual
                elif ": no" in linea or ": no" in linea:
                    #print(f"La IP es manual (estática).")
                    dhcp_found = False

        # Si no encuentra la línea, informa que no pudo determinarlo
        print("No se pudo determinar si la IP es DHCP o manual.")
        return None
    except Exception as e:
        # Si ocurre un error al ejecutar el comando, lo muestra
        print("Error al detectar DHCP:", e)
        return None
# Llama a la función para mostrar si la IP es DHCP o manual
#is_dhcp_enabled()


# ===============================
# Función para obtener el hostname del equipo
# ===============================
def get_hostname():
    try: 
        # Obtiene el nombre del equipo local
        hostname = socket.gethostname()
        return hostname
    except Exception as e:
        print("Error al obtener el nombre del equipo:", e)
        return None
#print(get_hostname())


def get_disk_capacities():
    """
    Devuelve lista con las capacidades de los discos (en GB).
    Ejemplo: ['500 GB', '1 TB']
    """
    discos = []
    try:
        for disk in psutil.disk_partitions(all=False):
            try:
                uso = psutil.disk_usage(disk.mountpoint)
                gb = round(uso.total / (1024**3))
                if gb >= 1024:
                    tb = gb / 1024
                    discos.append(f"{tb:.0f} TB")
                else:
                    discos.append(f"{gb} GB")
            except PermissionError:
                continue
    except Exception:
        return []
    # Eliminar duplicados (algunos discos montan varias letras)
    return list(dict.fromkeys(discos))


def get_computer_type():
    try:
        resultado = subprocess.run(
            ["wmic", "SystemEnclosure", "get", "ChassisTypes"],
            capture_output=True, text=True, encoding="latin-1"
        )
        # La salida contiene el modelo del equipo, se divide en líneas y se toma la segunda línea
        lineas = resultado.stdout.splitlines()
        for linea in lineas:
            linea = linea.strip().strip("{}")  # elimina espacios y llaves
            if linea.isdigit():  # Si la línea es un número
                type = int(linea)
                if type in [8, 9, 10, 14, 30]:
                    return "Portátil"
                elif type in [13,35]:
                    return "Todo en uno"
                elif type in [3, 4, 5, 6, 7, 15]:
                    return "Escritorio"
                else:
                    return "Desconocido"
    except Exception as e:
        print("Error al obtener el tipo de equipo:", e)
        return "Error al obtener tipo de equipo"
#print(get_computer_type())

def get_computer_model():
    try:
        resultado = subprocess.run(
            ["wmic", "csproduct", "get", "name"],
            capture_output=True, text=True, encoding="latin-1"
        )
        # La salida contiene el nombre del producto, se divide en líneas y se toma la segunda línea
        lineas = resultado.stdout.splitlines()
        for linea in lineas:
            if linea.strip() and "Name" not in linea:  # Verifica que la línea no esté vacía
                return linea.strip()  # Devuelve el nombre del producto
    except Exception as e:
        print("Error al obtener el modelo del equipo:", e)
        return "Error al obtener modelo del equipo"
#print(get_computer_model())

def get_serial_number():
    try:
        resultado = subprocess.run(
            ["wmic", "bios", "get", "serialnumber"],
            capture_output=True, text=True, encoding="latin-1"
        )
        lineas = resultado.stdout.splitlines()
        for linea in lineas:
            if linea.strip() and "SerialNumber" not in linea:  # Verifica que la línea no esté vacía
                return linea.strip()  # Devuelve el número de serie
    except Exception as e:
        print("Error al obtener el número de serie del equipo:", e)
        return "Error al obtener número de serie del equipo"
#print(get_serial_number())

def get_computer_brand():
    try:
        resultado = subprocess.run(
            ["wmic", "csproduct", "get", "vendor"],
            capture_output=True, text=True, encoding="latin-1"
        )
        lineas = resultado.stdout.splitlines()
        for linea in lineas:
            if linea.strip() and "Vendor" not in linea:  # Verifica que la línea no esté vacía
                return linea.strip()  # Devuelve la marca del equipo
    except Exception as e:
        print("Error al obtener la marca del equipo:", e)
        return "Error al obtener marca del equipo"
#print(get_computer_brand())

def get_computer_os():
    try:
        resultado = subprocess.run(
            ["wmic", "os", "get", "caption"],
            capture_output=True, text=True, encoding="latin-1"
        )
        lineas = resultado.stdout.splitlines()
        for linea in lineas:
            if linea.strip() and "Caption" not in linea:  # Verifica que la línea no esté vacía
                return linea.strip()  # Devuelve el nombre del sistema operativo
    except Exception as e:
        print("Error al obtener el sistema operativo:", e)
        return "Error al obtener sistema operativo"
# print(get_computer_os())

def get_computer_architecture():
    return platform.architecture()[0]
#print(get_computer_architecture())
def get_computer_processor():
    try:
        resultado = subprocess.run(
            ["wmic", "cpu", "get", "name"],
            capture_output=True, text=True, encoding="latin-1"
        )
        lineas = resultado.stdout.splitlines()
        for linea in lineas:
            if linea.strip() and "Name" not in linea:  # Verifica que la línea no esté vacía
                return linea.strip()  # Devuelve el nombre del procesador
    except Exception as e:
        print("Error al obtener el procesador del equipo:", e)
        return "Error al obtener procesador del equipo"
#print(get_computer_processor())

def get_computer_storage():
    total, used, free = shutil.disk_usage("/")
    return f"Total: {total // (2**30)} GiB"
#, Used: {used // (2**30)} GiB, Free: {free // (2**30)} GiB

def get_total_memory():
#34128322560 ÷ (1024³) = 31.78 GB
    resultado = subprocess.run(
        ["wmic", "ComputerSystem", "get", "TotalPhysicalMemory"],
        capture_output=True, text=True, encoding="latin-1"
    )
    lineas = resultado.stdout.splitlines()
    for linea in lineas:
        linea = linea.strip()
        if linea.isdigit():
            ram_gb = float(linea) / (1024 ** 3)
            return f"{ram_gb:.2f} GB" # retorno la ram com maximo 2 decimales
#print(get_total_memory())        

# ===============================

def get_system_info():
    hostname = get_hostname()
    computer_type = get_computer_type()
    computer_brand = get_computer_brand()
    computer_model = get_computer_model()
    serial_number = get_serial_number()
    computer_os = get_computer_os()
    computer_architecture = get_computer_architecture()
    computer_processor = get_computer_processor()
    computer_storage = get_computer_storage()
    computer_memory = get_total_memory()


    print(f"hostname: {hostname}")
    print(f"computer_type: {computer_type}")
    print(f"computer_brand: {computer_brand}")
    print(f"computer_model: {computer_model}")
    print(f"serial_number: {serial_number}")
    print(f"computer_os: {computer_os}")
    print(f"computer_architecture: {computer_architecture}")
    print(f"computer_processor: {computer_processor}")
    print(f"computer_storage: {computer_storage}")
    print(f"computer_memory: {computer_memory}")
    print(f"ip and dhcp: {is_dhcp_enabled()}")
#get_system_info()

'''
PALABRAS CLAVE:
- socket: Módulo para trabajar con sockets en Python.
- gethostname: Obtiene el nombre del equipo local.
- gethostbyname: Obtiene la dirección IP asociada al nombre del equipo.
- AF_INET: Indica que se utilizará IPv4.
- SOCK_DGRAM: Indica que se utilizará el protocolo UDP.
- UDP: Protocolo de datagramas de usuario, utilizado para enviar mensajes sin conexión.
- IP: Protocolo de Internet, que es el protocolo principal para la comunicación en redes.
- DHCP: Protocolo de configuración dinámica de host, utilizado para asignar direcciones IP a dispositivos en una red.

###FUNCIONES A TENER EN CUENTA###
- get_ip_address: Función que obtiene la dirección IP local del equipo.
- socket: Módulo que permite la creación de sockets para la comunicación en red
- gethostname: Método que obtiene el nombre del equipo local.
- gethostbyname: Método que obtiene la dirección IP asociada al nombre del equipo.
- AF_INET: Constante que indica que se utilizará IPv4.
- SOCK_DGRAM: Constante que indica que se utilizará el protocolo UDP.
- connect: Método que establece una conexión a un servidor especificado por su dirección IP y puerto.
- getsockname: Método que obtiene la dirección IP y el puerto asociados al socket.
#nombre_equipo = socket.gethostname() esto devolverá el nombre del equipo
#ip = socket.gethostbyname(nombre_equipo) esto devolverá la dirección IP local
#print(f"Nombre del equipo: {nombre_equipo}"

###TIPOS DE IP###
- IP local:
Ejemplo: 192.168.1.23
Solo visible en tu red local.
- IP pública:
Ejemplo: 181.45.123.99
Visible en Internet.
- IP loopback:
Siempre: 127.0.0.1
Solo para pruebas locales.


| Etiqueta     | Significado                                                    |
| ------------ | -------------------------------------------------------------- |
| **TODO**     | Algo pendiente por hacer.                                      |
| **FIXME**    | Algo que está roto o mal y hay que corregir.                   |
| **BUG**      | Indica un error conocido en el código.                         |
| **NOTE**     | Un comentario importante a tener en cuenta.                    |
| **HACK**     | Solución temporal o poco elegante que se debe mejorar.         |
| **XXX**      | Advertencia fuerte de que algo puede estar mal o es peligroso. |
| **OPTIMIZE** | Indica que una parte del código se puede optimizar.            |
# TODO: Implementar función de backup
# FIXME: Esta función falla si el archivo no existe
# NOTE: Usar solo en Windows
# BUG: Causa pérdida de datos si el archivo está abierto
# HACK: Forzamos el cierre de procesos aquí
# XXX: No usar en producción
# OPTIMIZE: Reducir uso de memoria

| Unidad         | Símbolo | Equivalencia                  |
| -------------- | ------- | ----------------------------- |
| **1 Byte**     | **B**   | 1 byte                        |
| **1 Kilobyte** | **KB**  | 1024 bytes                    |
| **1 Megabyte** | **MB**  | 1024 KB = 1 048 576 bytes     |
| **1 Gigabyte** | **GB**  | 1024 MB = 1 073 741 824 bytes |

34128322560 bytes
Bytes -> Kilobytes(KB)
34128322560 ÷ 1024 = 33332440 KB
KB -> Megabytes(MB)
33332440 ÷ 1024 = 32558.24 MB
MB -> Gigabytes(GB)
32558.24 ÷ 1024 = 31.78 GB

'''