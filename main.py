from audit import aplicaciones

if __name__ == "__main__":

    while True:
    
        print("---Inicio de la auditoria---")
        print("1. Verificar aplicaciones")
        print("2. Salir")
        opcion = input("Selecciona una opcion: ")

        match opcion:
            case "1":
                aplicaciones.verificar_aplicaciones("adobe")
                aplicaciones.verificar_aplicaciones("java")
                aplicaciones.verificar_aplicaciones("365")
            case "2":
                print("borrando temporales...")
            case "3":
                print("Saliendo de la auditoria...")
                break
            case _:
                print("Opcion no valida. Intente de nuevo.")
