#!/usr/bin/env bash
# Local Linux installation: Python core plus optional prebuilt/compiled Go worker.
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
APP="${XDG_DATA_HOME:-$HOME/.local/share}/shadowhunter"
BIN="$HOME/.local/bin"
STAGING=""

if ! command -v python3 >/dev/null 2>&1 || \
   ! python3 -c 'import sys; sys.exit(sys.version_info < (3,11))'; then
  echo "ShadowHunter needs Python 3.11+ (normally provided by Kali/Parrot/Ubuntu)." >&2
  exit 1
fi
if [[ ! -f "$ROOT/shadowhunterkit/cli.py" ]]; then
  echo "Run this installer from the unpacked ShadowHunter project." >&2
  exit 1
fi
mkdir -p -- "$(dirname "$APP")" "$BIN"
if [[ -L "$APP" ]] || { [[ -e "$APP" ]] && [[ ! -f "$APP/.shadowhunter-managed" ]]; }; then
  echo "Refusing to replace an unmanaged application directory: $APP" >&2
  exit 1
fi
if [[ -L "$BIN/shadowhunter" ]] || { [[ -e "$BIN/shadowhunter" ]] && \
    ! grep -q '^# ShadowHunter managed launcher$' "$BIN/shadowhunter"; }; then
  echo "Refusing to replace an unrelated command: $BIN/shadowhunter" >&2
  exit 1
fi

STAGING="$(mktemp -d "${APP}.stage.XXXXXX")"
trap '[[ -z "$STAGING" ]] || rm -rf -- "$STAGING"' EXIT
cp -R -- "$ROOT/shadowhunterkit" "$STAGING/shadowhunterkit"
printf 'ShadowHunter managed installation\n' > "$STAGING/.shadowhunter-managed"
mkdir -p -- "$STAGING/bin"

ARCH="$(uname -m)"
case "$ARCH" in
  x86_64|amd64) ARCH="amd64" ;;
  aarch64|arm64) ARCH="arm64" ;;
  *) ARCH="" ;;
esac

ENGINE="Python fallback"
if [[ -n "$ARCH" && -f "$ROOT/dist/linux_$ARCH/shadowhunter-worker" ]]; then
  cp -- "$ROOT/dist/linux_$ARCH/shadowhunter-worker" "$STAGING/bin/shadowhunter-worker"
  chmod 755 "$STAGING/bin/shadowhunter-worker"
  ENGINE="Precompiled Go ($ARCH)"
elif command -v go >/dev/null 2>&1 && [[ -f "$ROOT/cmd/evidencehash/main.go" ]]; then
  if (cd -- "$ROOT" && CGO_ENABLED=0 go build -trimpath \
    -o "$STAGING/bin/shadowhunter-worker" ./cmd/evidencehash); then
    ENGINE="Go compiled during installation"
  else
    echo "Go compilation unavailable; evidence hashing will use Python."
  fi
fi

if [[ -d "$APP" ]]; then
  rm -rf -- "$APP"
fi
mv -- "$STAGING" "$APP"
STAGING=""

cat > "$BIN/shadowhunter" <<'SHADOWHUNTER_LAUNCHER'
#!/bin/sh
# ShadowHunter managed launcher
APP="${XDG_DATA_HOME:-$HOME/.local/share}/shadowhunter"
export PYTHONPATH="$APP${PYTHONPATH:+:$PYTHONPATH}"
exec python3 -m shadowhunterkit "$@"
SHADOWHUNTER_LAUNCHER
chmod 755 "$BIN/shadowhunter"

if [[ ! -e "$BIN/shunter" && ! -L "$BIN/shunter" ]] || \
   [[ -L "$BIN/shunter" && "$(readlink "$BIN/shunter")" == "shadowhunter" ]]; then
  ln -sfn -- shadowhunter "$BIN/shunter"
fi

echo "✅ Installed: $BIN/shadowhunter"
echo "   Evidence engine: $ENGINE"
if [[ ":$PATH:" != *":$BIN:"* ]]; then
  echo "   Start with: $BIN/shadowhunter"
else
  echo "   Start with: shadowhunter"
fi
