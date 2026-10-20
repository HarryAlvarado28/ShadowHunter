#!/usr/bin/env bash
# Optional Go experiment: not needed for ShadowHunter's Python CLI.
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
if ! command -v go >/dev/null 2>&1; then
  echo "Go not installed; this optional build was skipped." >&2
  exit 2
fi
mkdir -p dist
go build -trimpath -o dist/shadowhunter-osint ./cmd/osint.go
echo "✅ Optional Go prototype: dist/shadowhunter-osint"
echo "Main CLI (no Go dependency): python3 -m shadowhunterkit"
