import subprocess
import os

def run():
    print("\n[🕵️] Ejecutando módulo OSINT en Go...\n")

    cmd_path = os.path.join(os.path.dirname(__file__), '..', 'cmd', 'osint')

    if os.path.isfile(cmd_path):
        subprocess.run([cmd_path])
    else:
        print("❌ Ejecutable del módulo OSINT no encontrado. Asegúrate de compilarlo primero.")
