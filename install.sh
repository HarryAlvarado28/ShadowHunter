#!/bin/bash

# Ruta destino
BIN_PATH="/usr/local/bin"
INSTALL_NAME="shadowhunter"
ALIAS_NAME="shunter"
SCRIPT_NAME="shadowhunter.py"
PROFILE_GLOBAL="/etc/profile.d/shunter.sh"

echo "[*] Iniciando instalación de ShadowHunter..."

# Verifica si el archivo principal existe
if [ ! -f "$SCRIPT_NAME" ]; then
  echo "❌ Error: No se encuentra '$SCRIPT_NAME' en el directorio actual."
  exit 1
fi

# Copiar archivo al directorio bin y hacerlo ejecutable
echo "[*] Copiando archivo ejecutable a $BIN_PATH..."
sudo cp "$SCRIPT_NAME" "$BIN_PATH/$INSTALL_NAME"
sudo chmod +x "$BIN_PATH/$INSTALL_NAME"

# Crear alias global (para todos los shells compatibles)
echo "[*] Configurando alias global '$ALIAS_NAME' para '$INSTALL_NAME'..."

if [ -w /etc/profile.d ]; then
  sudo bash -c "cat > $PROFILE_GLOBAL" <<EOF
#!/bin/sh
alias $ALIAS_NAME="$INSTALL_NAME"
EOF
  sudo chmod +x $PROFILE_GLOBAL
  echo "[+] Alias global instalado exitosamente en $PROFILE_GLOBAL"
else
  echo "⚠️ No se pudo escribir en /etc/profile.d/. Se instalará alias local para el usuario actual."
  
  # Detectar shell y agregar al archivo correspondiente del usuario actual
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

  echo "alias $ALIAS_NAME=\"$INSTALL_NAME\"" >> "$PROFILE_FILE"
  echo "[+] Alias agregado al archivo de perfil del usuario: $PROFILE_FILE"
  echo "🔁 Ejecuta 'source $PROFILE_FILE' o reinicia tu terminal para aplicar los cambios."
fi

echo ""
echo "✅ Instalación completada."
echo "👉 Ahora puedes ejecutar la herramienta con:"
echo "    ➤ $INSTALL_NAME"
echo "    ➤ $ALIAS_NAME (alias)"
