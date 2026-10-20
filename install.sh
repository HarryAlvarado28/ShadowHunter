#!/usr/bin/env bash
# Rootless, dependency-free Linux installation for ShadowHunter.
set -euo pipefail

PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/shadowhunter"
BIN_DIR="$HOME/.local/bin"
STAGING=""

if ! command -v python3 >/dev/null 2>&1; then
  echo "Error: Python 3.11+ is required." >&2
  exit 1
fi
if ! python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)'; then
  echo "Error: Python 3.11+ required; current: $(python3 --version)." >&2
  exit 1
fi
if [[ ! -f "$PROJECT_DIR/shadowhunterkit/cli.py" ]]; then
  echo "Error: run this installer from the cloned ShadowHunter project." >&2
  exit 1
fi

mkdir -p "$(dirname "$DATA_DIR")" "$BIN_DIR"
if [[ -e "$DATA_DIR" && ! -f "$DATA_DIR/.shadowhunter-managed" ]]; then
  echo "Refusing to overwrite unmanaged directory: $DATA_DIR" >&2
  exit 1
fi

STAGING="$(mktemp -d "${DATA_DIR}.staging.XXXXXX")"
trap '[[ -z "$STAGING" ]] || rm -rf -- "$STAGING"' EXIT
cp -R -- "$PROJECT_DIR/shadowhunterkit" "$STAGING/shadowhunterkit"
printf 'Managed ShadowHunter installation\n' > "$STAGING/.shadowhunter-managed"

# Replace only a previous installation bearing our own marker.
if [[ -d "$DATA_DIR" ]]; then
  rm -rf -- "$DATA_DIR"
fi
mv -- "$STAGING" "$DATA_DIR"
STAGING=""

cat > "$BIN_DIR/shadowhunter" <<'SHADOWHUNTER_LAUNCHER'
#!/bin/sh
# ShadowHunter managed launcher
APP_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/shadowhunter"
export PYTHONPATH="$APP_DIR${PYTHONPATH:+:$PYTHONPATH}"
exec python3 -m shadowhunterkit "$@"
SHADOWHUNTER_LAUNCHER
chmod 755 "$BIN_DIR/shadowhunter"
ln -sfn -- shadowhunter "$BIN_DIR/shunter"

echo "✅ ShadowHunter installed for current user; no sudo or pip used."
echo "   $BIN_DIR/shadowhunter"
echo "   $BIN_DIR/shunter"
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
  echo "Add $BIN_DIR to PATH or run the full path above."
fi
echo "Start: shadowhunter    |    Health check: shadowhunter doctor"
