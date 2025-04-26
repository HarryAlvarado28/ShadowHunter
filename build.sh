#!/bin/bash

set -e  # Detiene si hay errores

echo "[*] Compilando binarios Go de ShadowHunter..."

# Ruta al binario OSINT
OSINT_SRC="cmd/osint.go"
OSINT_BIN="cmd/osint"

if [ -f "$OSINT_SRC" ]; then
  echo "[*] Compilando módulo OSINT..."
  go build -o "$OSINT_BIN" "$OSINT_SRC"
  echo "[+] Módulo OSINT compilado con éxito: $OSINT_BIN"
else
  echo "❌ No se encontró el archivo fuente: $OSINT_SRC"
  exit 1
fi

# Aquí puedes agregar más módulos Go si luego los necesitas
# Ejemplo:
# PAYLOADS_SRC="cmd/payload.go"
# go build -o cmd/payload "$PAYLOADS_SRC"

echo "\n✅ Compilación finalizada. Ejecuta ./install.sh para instalar."
