from audit import aplicaciones
from audit import pc_info
from audit import limpieza

###FUNCIONES###
def search(data = None):
    resultado = aplicaciones.verificar_aplicaciones(data)
    if resultado:
        pass
    else:
        print(f"No tiene {data}")
###############

if __name__ == "__main__":

    while True:
        print("---Inicio de la auditoria---")
        print("1. Verificar aplicaciones")
        print("2. Limpieza(temp y papelera)")
        print("3. Obtener dirección IP local")
        print("4. Hostname del equipo")
        print("5. Datos del equipo")
        print("9. Salir")
        opcion = input("Selecciona una opcion: ")

        match opcion:
            case "1":
                search("java")
                search("kaspersky")
                search("adobe")
                search("winrar")
            case "2":
                print("🧹Limpiando archivos temporales...")
                limpieza.limpiar_todo()
            case "3":
                print("Obteniendo dirección IP local...")
                pc_info.is_dhcp_enabled()
            case "4":
                print("Obteniendo hostname del equipo...")
                pc_info.get_hostname()
            case "5":
                print("Obteniendo datos de equipo...")
                print('###########################')
                pc_info.get_system_info()
                print('###########################')
            case "9":
                print("Saliendo de la auditoria...")
                break
            case _:
                print("Opcion no valida. Intente de nuevo.")

