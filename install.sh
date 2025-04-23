#!/bin/bash

echo "[*] Instalando ShadowHunter..."

# Copia el archivo principal al directorio bin del sistema
sudo cp shadowhunter.py /usr/local/bin/shadowhunter

# Da permisos de ejecución
sudo chmod +x /usr/local/bin/shadowhunter

echo "[+] Instalación completada. Ejecuta con: shadowhunter"
