import socket
import subprocess

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
print("Tu dirección IP local es:", get_ip_address())

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
                        print(f"La IP {ip_obj} está asignada por DHCP (automática).")
                        return True
                    elif dhcp_found == False:
                        print(f"La IP {ip_obj} es manual (estática).")
                        return False
                    return True
                break
            if "dhcp habilitado" in linea or "dhcp enabled" in linea:
                # Si encuentra la línea, revisa si dice 'sí' o 'yes' (DHCP activado)
                if ": s¡" in linea or ": yes" in linea:
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
is_dhcp_enabled()

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
'''