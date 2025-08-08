import os
import shutil
import ctypes
import tempfile

def cleaner(ruta):
    # Directorio de archivos temporales
    # ELIMINAR TODO DENTRO DE LA CARPETA SIN ELIMINAR LA CARPETA
    if not os.path.exists(ruta):
        print(f'La ruta {ruta} no existe.')
        return

    errores = 0 
    eliminados = 0

    for item in os.listdir(ruta):
        full_path = os.path.join(ruta, item)
        try:
            if os.path.isfile(full_path) or os.path.islink(full_path):
                os.remove(full_path)
                eliminados += 1
            elif os.path.isdir(full_path):#si es un directorio(carpeta), lo eliminamos recursivamente
                shutil.rmtree(full_path)
                eliminados += 1
        except Exception as e:
            print(f'⚠️ Error al eliminar {full_path}: {e}')
            errores += 1
    print(f"✅ Limpieza en {ruta} terminada. Archivos eliminados: {eliminados}, errores: {errores}")

def limpiar_papelera():
    # Limpia la papelera de reciclaje
    try:
        # Utiliza la función SHEmptyRecycleBin de la biblioteca shell32 de Windows que limpia la papelera
        print("🗑️ Limpiando papelera de reciclaje...")
        ctypes.windll.shell32.SHEmptyRecycleBinW(0, None, 0x00000001)
        print("✅ Papelera de reciclaje vaciada.")
    except Exception as e:
        print(f"⚠️ Error al vaciar la papelera de reciclaje: {e}")

'''
los parámetros (0, None, 0) significan

0: El identificador de ventana padre (hwnd).
0 significa que no hay ventana asociada (no se muestra como parte de ninguna ventana).

None: La ruta de la papelera a vaciar (pszRootPath).
None significa que vacía la papelera de todas las unidades del sistema.

0: Las opciones de limpieza (dwFlags).
0 significa que se usan las opciones por defecto: muestra confirmación, barra de progreso y sonido.

0x00000001 (SHERB_NOCONFIRMATION): No pedir confirmación al usuario.
0x00000002 (SHERB_NOPROGRESSUI): No mostrar barra de progreso.
0x00000004 (SHERB_NOSOUND): No reproducir sonido al vaciar.
'''


'''
    def is_admin():
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
'''
def limpiar_temporales():
    ruta_temp = tempfile.gettempdir()
    # Directorio de archivos temporales
    #print("🧹Limpiando archivos temporales...")
    cleaner(ruta_temp)

def limpiar_todo():
    # Limpia todos los archivos temporales y la papelera de reciclaje
    limpiar_temporales()
    limpiar_papelera()