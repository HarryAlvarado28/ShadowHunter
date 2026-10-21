#!/usr/bin/env bash
# Optional native build for Linux; Python features work without Go.
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
if ! command -v go >/dev/null 2>&1; then
  echo "Go is optional. Install a prebuilt bundle or use Python fallback." >&2
  exit 2
fi
case "$(uname -m)" in
  x86_64|amd64) ARCH="amd64" ;;
  aarch64|arm64) ARCH="arm64" ;;
  *) echo "Unsupported native Linux architecture." >&2; exit 2 ;;
esac
mkdir -p "dist/linux_$ARCH"
GOTOOLCHAIN=local CGO_ENABLED=0 GOOS=linux GOARCH="$ARCH" go build -trimpath \
  -o "dist/linux_$ARCH/shadowhunter-worker" ./cmd/evidencehash
echo "✅ Built dist/linux_$ARCH/shadowhunter-worker"
