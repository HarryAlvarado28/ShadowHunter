#!/bin/bash

INSTALL_NAME="shadowhunter"
ALIAS_NAME="shunter"
BIN_PATH="/usr/local/bin"
PROFILE_GLOBAL="/etc/profile.d/shunter.sh"

echo "[*] Iniciando desinstalación de ShadowHunter..."

# Eliminar el ejecutable
if [ -f "$BIN_PATH/$INSTALL_NAME" ]; then
  echo "[*] Eliminando ejecutable: $BIN_PATH/$INSTALL_NAME"
  sudo rm -f "$BIN_PATH/$INSTALL_NAME"
else
  echo "⚠️ Ejecutable no encontrado en $BIN_PATH."
fi

# Eliminar alias global
if [ -f "$PROFILE_GLOBAL" ]; then
  echo "[*] Eliminando alias global en $PROFILE_GLOBAL"
  sudo rm -f "$PROFILE_GLOBAL"
else
  echo "⚠️ Alias global no encontrado en $PROFILE_GLOBAL"
fi

# Limpiar alias local del usuario actual
SHELL_NAME=$(basename "$SHELL")
PROFILE_FILE=""

case "$SHELL_NAME" in
  bash)
    PROFILE_FILE="$HOME/.bashrc"
    ;;
  zsh)
    PROFILE_FILE="$HOME/.zshrc"
    ;;
  fish)
    PROFILE_FILE="$HOME/.config/fish/config.fish"
    ;;
  *)
    PROFILE_FILE="$HOME/.profile"
    ;;
esac

if [ -f "$PROFILE_FILE" ]; then
  if grep -q "alias $ALIAS_NAME=" "$PROFILE_FILE"; then
    echo "[*] Eliminando alias local del usuario en $PROFILE_FILE"
    sed -i "/alias $ALIAS_NAME=/d" "$PROFILE_FILE"
  fi
fi

echo ""
echo "✅ Desinstalación completada."
echo "ℹ️ Si aún no ves los cambios, ejecuta 'source $PROFILE_FILE' o reinicia la terminal."
