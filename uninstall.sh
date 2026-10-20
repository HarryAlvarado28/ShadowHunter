#!/usr/bin/env bash
# Remove only files owned by ShadowHunter's user-level installer.
set -euo pipefail

DATA_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/shadowhunter"
BIN_DIR="$HOME/.local/bin"

if [[ -f "$DATA_DIR/.shadowhunter-managed" ]]; then
  rm -rf -- "$DATA_DIR"
  echo "Removed managed application directory."
else
  echo "No managed application directory found (left untouched)."
fi

if [[ -f "$BIN_DIR/shadowhunter" ]] &&
   grep -q '^# ShadowHunter managed launcher$' "$BIN_DIR/shadowhunter"; then
  rm -- "$BIN_DIR/shadowhunter"
  echo "Removed managed launcher."
fi

if [[ -L "$BIN_DIR/shunter" ]] &&
   [[ "$(readlink "$BIN_DIR/shunter")" == "shadowhunter" ]]; then
  rm -- "$BIN_DIR/shunter"
fi

echo "✅ Uninstalled. Workspace history was intentionally preserved."
echo "   To delete it manually: ${XDG_STATE_HOME:-$HOME/.local/state}/shadowhunter"
