#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="$ROOT/logs"
mkdir -p "$LOG_DIR"

if pgrep -f "python core/brain.py" >/dev/null; then
  echo "Flask brain already appears to be running."
else
  echo "Starting Flask brain in background..."
  setsid -f bash -lc "cd '$ROOT/python' && source venv/bin/activate && python core/brain.py >> '$LOG_DIR/brain.log' 2>&1"
fi

if pgrep -f "deathai-go-server" >/dev/null; then
  echo "Go front door already appears to be running."
else
  echo "Building and starting Go front door in background..."
  GO_BIN="${GO_BIN:-/usr/local/go/bin/go}"
  if [[ ! -x "$GO_BIN" ]]; then
    GO_BIN="$(command -v go)"
  fi
  cd "$ROOT/go"
  "$GO_BIN" build -o /tmp/deathai-go-server main.go
  setsid -f /tmp/deathai-go-server >> "$LOG_DIR/go-server.log" 2>&1
fi

echo "Open http://localhost:8080"
echo "Logs:"
echo "  $LOG_DIR/brain.log"
echo "  $LOG_DIR/go-server.log"
