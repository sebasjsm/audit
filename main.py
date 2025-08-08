from audit import aplicaciones

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
        print("2. Borrar archivos temporales")
        print("3. Obtener dirección IP local")
        print("4. Salir")
        opcion = input("Selecciona una opcion: ")

        match opcion:
            case "1":
                search("java")
                search("kaspersky")
                search("adobe")
                search("winrar")
                
            case "2":
                print("borrando temporales...")
            case "3":
                print("Saliendo de la auditoria...")
                aplicaciones.verificar_aplicaciones()
                break
            case _:
                print("Opcion no valida. Intente de nuevo.")

