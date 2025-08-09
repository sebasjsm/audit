from audit import aplicaciones
from audit import pc_info
from audit import limpieza
import ctypes
import sys

###FUNCIONES###
def search(data = None):
    resultado = aplicaciones.verificar_aplicaciones(data)
    if resultado:
        pass
    else:
        print(f"No tiene {data}")

def run_as_admin():
    # Verifica si el script ya se está ejecutando como administrador
    if ctypes.windll.shell32.IsUserAnAdmin():
        # Si ya es administrador, devuelve True para que el programa continúe
        return True
    else:
        # Si no es administrador, relanza el script solicitando privilegios elevados
        ctypes.windll.shell32.ShellExecuteW(
            None,                 # No hay ventana padre
            "runas",              # Acción 'runas' -> Ejecutar como administrador
            sys.executable,       # Ruta al ejecutable de Python (o al .exe si está compilado)
            " ".join(sys.argv),   # Pasa los mismos argumentos que tenía el script original
            None,                 # Directorio de trabajo (None = actual)
            1                     # Muestra la ventana normalmente (1 = SW_SHOWNORMAL)
        )
        # Cierra el proceso actual, ya que el nuevo con permisos de admin se encargará
        sys.exit()

###############

if __name__ == "__main__":
    #run_as_admin()  # Llama a la función para verificar y elevar permisos si es necesario
    while True:
        print("---Inicio de la auditoria---")
        print("1. Verificar aplicaciones")
        print("2. Datos del equipo")
        print("3. Obtener dirección IP local")
        print("4. Hostname del equipo")
        print("5. Limpieza(temp y papelera)")
        print("9. Salir")
        opcion = input("Selecciona una opcion: ")

        match opcion:
            case "1":
                search("java")
                search("kaspersky")
                search("adobe")
                search("winrar")
            case "2":
                print("Obteniendo datos de equipo...")
                print('###########################')
                pc_info.get_system_info()
                print('###########################')
            case "3":
                print("Obteniendo dirección IP local...")
                print(pc_info.is_dhcp_enabled())
            case "4":
                print("Obteniendo hostname del equipo...")
                print(pc_info.get_hostname())
            case "5":
                print("🧹Limpiando archivos temporales...")
                limpieza.limpiar_todo()
            case "9":
                print("Saliendo de la auditoria...")
                break
            case _:
                print("Opcion no valida. Intente de nuevo.")



'''
| Verbo     | Qué hace                                                                  |
| --------- | ------------------------------------------------------------------------- |
| `"open"`  | Acción por defecto (abrir el archivo o ejecutar el programa normalmente). |
| `"edit"`  | Abre el archivo para editarlo (si hay un editor asociado).                |
| `"print"` | Imprime el archivo con la impresora predeterminada.                       |
| `"runas"` | Ejecuta el archivo o programa como administrador (eleva privilegios UAC). |
'''