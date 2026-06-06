#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ -f "$ROOT/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$ROOT/.env"
  set +a
fi

cd "$ROOT/go"

GO_BIN="${GO_BIN:-/usr/local/go/bin/go}"
if [[ ! -x "$GO_BIN" ]]; then
  GO_BIN="$(command -v go)"
fi

echo "Starting DEATH.AI Go front door on http://localhost:${PORT:-8080}"
exec "$GO_BIN" run main.go
