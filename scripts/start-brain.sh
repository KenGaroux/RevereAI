#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ -f "$ROOT/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$ROOT/.env"
  set +a
fi

cd "$ROOT/python"
source venv/bin/activate

echo "Starting Reverie Flask brain on http://0.0.0.0:5000"
exec python core/brain.py
