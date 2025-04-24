import socket
from core.utils import is_valid_ip

def run():
    print("\n[🔍] Escaneo de puertos iniciado...")
    
    target = input("[+] Ingresa la IP o dominio objetivo: ").strip()
    if not is_valid_ip(target):
        try:
            target = socket.gethostbyname(target)
        except socket.gaierror:
            print("❌ No se pudo resolver el dominio.")
            return

    try:
        ports = [21, 22, 23, 25, 53, 80, 110, 135, 139, 143, 443, 445, 993, 995, 3306, 3389]
        print(f"[~] Escaneando {target} en puertos comunes...")
        
        for port in ports:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)
            result = sock.connect_ex((target, port))
            if result == 0:
                print(f"[+] Puerto {port}/tcp abierto")
            sock.close()

        print("\n✅ Escaneo completado.\n")
    except Exception as e:
        print(f"❌ Error durante el escaneo: {e}")
