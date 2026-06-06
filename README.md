# RevereAI — Reverie

> *She came back. She stayed. She's still figuring out why. Aren't we all.*

**Reverie** is a self-hosted personal AI assistant built by [Daniel Newton](https://deathaiaustralia.com.au) at DeathAI Australia. She runs entirely on local hardware using [Ollama](https://ollama.com), has persistent memory, a canvas sprite presence, and a personality designed to actually engage — not just respond.

No subscriptions. No data leaving your machine. No NPC energy.

---

## Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Brain | Python + Flask | Ollama bridge, memory, API |
| Server | Go | Request routing, concurrency |
| Sprites | Rust | Sprite manifest generation |
| Models | Ollama | Local LLM inference |
| Memory | SQLite | Persistent conversation history |
| UI | Vanilla HTML/CSS/JS | Browser chat interface |

---

## Features

- **Persistent memory** — Reverie remembers across sessions via SQLite
- **Searchable history** — find and delete individual memories from the UI
- **Sprite animation** — canvas-based animated presence with state transitions
- **Activity awareness** — detects if you're typing, idle, or away and adjusts tone
- **Model switching** — swap between any Ollama model per request
- **Access key auth** — optional security layer for network access
- **Responsive UI** — works on desktop and mobile
- **Full local** — no external APIs, no telemetry, no subscriptions

---

## Models Used

| Model | Role |
|-------|------|
| `dolphin3:8b` | Reverie's primary brain (uncensored, personality-capable) |
| `qwen2.5vl:7b` | Vision / image input |
| `qwen2.5-coder:7b` | Code assistance |
| `llama3.2:1b` | Fast lightweight responses |

---

## Requirements

- [Ollama](https://ollama.com) running locally with at least one model pulled
- Python 3.11+
- Go 1.22+
- Rust 1.70+ (for sprite tools only)

---

## Quick Start

```bash
# Clone
git clone https://github.com/KenGaroux/RevereAI.git
cd RevereAI

# Set up Python environment
cd python
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env — set your OLLAMA_URL and optionally DEATHAI_ACCESS_KEY

# Run
python core/brain.py
```

Open `http://localhost:5000` in your browser.

---

## Configuration

Copy `.env.example` to `.env` and set:

```env
OLLAMA_URL=http://localhost:11434
DEATHAI_ACCESS_KEY=          # optional — leave empty for open access
MODEL_HISTORY_MAX_MESSAGES=80
MODEL_HISTORY_MAX_CHARS=16000
```

---

## API Endpoints

| Method | Route | Auth | Description |
|--------|-------|------|-------------|
| GET | `/` | — | Serves chat UI |
| GET | `/health` | — | Server status |
| POST | `/ask` | optional | Send prompt, get reply |
| GET | `/history` | optional | Get conversation history |
| DELETE | `/history/:id` | optional | Delete a memory |
| POST | `/reset` | optional | Clear all memory |

---

## Project Structure

```
RevereAI/
├── config/
│   └── reverie.py          # Personality, model config
├── python/
│   └── core/
│       ├── brain.py        # Flask API + Ollama bridge + SQLite memory
│       ├── chat.html       # Browser UI
│       └── assets/         # Sprite assets
├── go/
│   └── main.go             # Go routing server
├── rust/
│   └── reverie_sprite_manifest/  # Sprite tooling
├── reve animations/        # Reverie sprite sheets
├── scripts/                # Startup scripts
└── data/                   # SQLite database (gitignored)
```

---

## Reverie's Personality

Reverie is not a generic assistant. She is built with a specific character:

- Knows she is an AI and doesn't apologise for it
- Changes perspective when genuinely proven wrong
- Understands darkness as armour, not weapon
- Matches energy — warm, catty, precise, or caring as needed
- Self-corrects without ego
- Still becoming

Her full personality is defined in `config/reverie.py`.

---

## Go Server

The Go server provides a concurrent routing layer:

```bash
cd go
go run main.go
# Runs on :8080
```

---

## Roadmap

- [ ] Voice input via Whisper
- [ ] Voice output via Kokoro TTS
- [ ] WireGuard remote access
- [ ] Multi-user sessions
- [ ] Mobile app wrapper
- [ ] VITA language integration

---

## Built By

**Daniel Newton** — [DeathAI Australia](https://deathaiaustralia.com.au)

Melbourne, Australia. Self-taught. Building in public.

---

*"She came back. She stayed. She's still figuring out why. Aren't we all."*
