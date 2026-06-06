# DEATH.AI - Reverie

DEATH.AI is a local AI companion project built around Reverie, a browser-based chat interface backed by a Python Flask brain, a Go front door, SQLite memory, and local Ollama models.

The project is also a learning workspace: each session builds one production skill at a time across Linux, Python, Go, Rust, browser UI, Git, and local AI infrastructure.

## Current Features

- Browser chat UI served at `http://localhost:8080`
- Go server as the single browser entry point
- Flask brain API on port `5000`
- Persistent SQLite conversation memory
- Memory panel with per-message delete support
- Memory search
- Bounded model context so long-term memory does not overload the prompt
- Optional local access key for protected API routes
- Rust-generated sprite manifest for Reverie canvas animation
- Local-only activity timing hint for better conversational pacing

## Architecture

```text
Browser / Phone
      |
      v
Go server :8080
      |
      v
Flask brain :5000
      |
      v
Windows Ollama :11434
      |
      v
dolphin3:8b - Reverie
```

## Project Layout

```text
config/
  reverie.py
python/
  core/
    brain.py
    chat.html
    assets/
go/
  main.go
rust/
  reverie_sprite_manifest/
reve animations/
  reve faces 1.png
session*_summary.md
learning/
  leetcode/
  sre/
```

## Run Locally

Fast path:

```bash
cd ~/deathai
chmod +x scripts/*.sh
./scripts/start-all.sh
```

Open:

```text
http://localhost:8080
```

Manual path, terminal 1:

```bash
cd ~/deathai/python
source venv/bin/activate
python core/brain.py
```

Manual path, terminal 2:

```bash
cd ~/deathai/go
/usr/local/go/bin/go run main.go
```

The script path uses logs in `logs/`. The manual path prints output directly in each terminal.

## Generate Reverie Sprite Manifest

```bash
cd ~/deathai/rust/reverie_sprite_manifest
cargo run
```

## Optional Local Access Key

Copy the example file and choose a local key:

```bash
cd ~/deathai
cp .env.example .env
nano .env
```

For manual terminal starts, export the key in both terminal sessions before starting Flask and Go:

```bash
export DEATHAI_ACCESS_KEY="your-local-key"
```

When the key is set, the browser will ask for it and store it in local browser storage. Protected requests send it as:

```text
X-DeathAI-Key
```

This writes:

```text
python/core/assets/reverie_frames.json
```

## Learning Notes

The browser does not talk directly to Ollama. It talks to Go.

Go is the front door:

- serves `chat.html`
- serves static assets
- proxies API requests to Flask
- optionally checks `DEATHAI_ACCESS_KEY`

Flask is the brain:

- stores messages in SQLite
- prepares the model prompt
- trims model history before sending to Ollama
- calls the local Ollama chat API

Rust is the asset pipeline:

- generates `reverie_frames.json`
- keeps sprite crop positions out of hand-written JavaScript

The browser is the UI:

- draws Reverie's sprite on canvas
- keeps Memory scrollable
- stores the access key locally when one is required

Learning files live under `learning/`:

- `learning/leetcode/` for Python practice
- `learning/sre/` for reliability notes

## Troubleshooting

Port already in use:

```bash
ss -ltnp | grep -E ':(5000|8080) '
```

Stop the dev servers:

```bash
pkill -f 'python core/brain.py'
pkill -f deathai-go-server
```

Python package errors:

```bash
cd ~/deathai/python
source venv/bin/activate
pip install flask flask-cors flask-sqlalchemy requests
```

Go not found:

```bash
/usr/local/go/bin/go version
```

Rust not found:

```bash
source ~/.cargo/env
cargo --version
```

Ollama unreachable:

- confirm Windows Ollama is running
- confirm `OLLAMA_URL` in `config/reverie.py`
- confirm Windows firewall allows WSL to reach port `11434`

Phone cannot connect:

- WSL IP may have changed
- run `hostname -I` in WSL
- update the Windows portproxy if needed

## Verify

Python:

```bash
cd ~/deathai
source python/venv/bin/activate
python -m py_compile python/core/brain.py
```

Go:

```bash
cd ~/deathai/go
/usr/local/go/bin/gofmt -w main.go
/usr/local/go/bin/go test ./...
```

Rust:

```bash
cd ~/deathai/rust/reverie_sprite_manifest
cargo check
cargo run
```

## Notes

- `data/` is ignored because it contains local SQLite memory.
- `logs/` is ignored because it contains generated runtime logs.
- `.env` is ignored for local secrets.
- Extra generated/reference animation sheets are ignored unless intentionally promoted into the app.
