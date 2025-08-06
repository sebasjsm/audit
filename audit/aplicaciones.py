import winreg

def verificar_aplicaciones(filtro = None):
    keys = [r"SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall",
            r"SOFTWARE\\Wow6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall"
    ]

    for key_path in keys:
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
                for i in range(winreg.QueryInfoKey(key)[0]): # Obtiene el número de subclaves y [0] es el primero 
                    #de los valores que retorna QueryInfoKey siendo ese el número de subclaves
                    subkey_name = winreg.EnumKey(key, i) # Obtiene el nombre de la subclave en el índice i
                    try:
                        with winreg.OpenKey(key, subkey_name) as subkey:
                            display_name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                            if filtro and filtro.lower() not in display_name.lower():
                                continue
                            try:
                                display_version = winreg.QueryValueEx(subkey, "DisplayVersion")[0]
                            except FileNotFoundError:
                                display_version = "Version Desconocida"
                            print(f"{display_name} - Version: {display_version}")
                    except FileNotFoundError:
                        #print(f"Subclave {subkey_name} no tiene DisplayName.")
                        continue
        except FileNotFoundError:
            print(f"La clave {key_path} no existe.")
            continue