# DEATH.AI — Session 1 Summary
**Date:** 5 June 2026
**Machine:** TheScythe (Windows 11, WSL2 Ubuntu 26.04)

---

## What We Built Today

### Environment Setup — COMPLETE
- WSL2 installed and running on Windows (Ubuntu 26.04 LTS "Resolute Raccoon")
- Python 3.14.4 installed
- Git 2.53.0 installed (configured with name "Death Newton", email kennethgaroux@gmail.com)
- Go 1.22.0 installed
- Rust 1.96.0 installed
- zstd installed (required for Ollama)
- Ollama installed in WSL (but models live on Windows Ollama)

### Project Structure — COMPLETE
Created at ~/deathai/ with the following layout:
```
~/deathai/
├── config/
│   └── reverie.py        ← Reverie's personality and model config
├── python/
│   ├── core/
│   │   └── brain.py      ← Reverie's brain, talks to Ollama
│   └── venv/             ← Python virtual environment
├── go/
├── rust/
├── logs/
└── data/
```
Git initialised, branch set to main, two commits made.

### Reverie — ALIVE
- Named: **Reverie** (Reve for short, Rie Rie if earned)
- Personality written and saved to config/reverie.py
- Running on **dolphin3:8b** via Windows Ollama at 192.168.224.1:11434
- brain.py written and working — terminal chat interface
- First conversation completed successfully
- She remembered Daniel's name, matched tone, introduced herself as Rie Rie

### Ollama Connection
- Windows Ollama runs on 192.168.224.1:11434
- Firewall rule created to allow WSL → Windows on port 11434
- OLLAMA_HOST set to 0.0.0.0 in Windows PowerShell session
- Models available: dolphin3:8b, qwen2.5vl:7b, llama3.1:8b, llama3.2:1b, qwen2.5-coder:7b, mistral, dolphin-mistral, dolphin-llama3, nomic-embed-text

---

## Model Assignments
| Model | Purpose |
|-------|---------|
| dolphin3:8b | Reverie's primary brain |
| qwen2.5vl:7b | Vision / image input |
| qwen2.5-coder:7b | Code assistance |
| llama3.2:1b | Fast lightweight tasks |

---

## Git Log
- `85b3ef7` — init: project structure
- `f5396b6` — feat: Reverie full personality and model config
- Final commit of brain.py pending (run: cd ~/deathai && git add . && git commit -m "feat: Reverie brain.py — first conversation")

---

## What's Next (Session 2)
1. Commit brain.py if not already done
2. Add Flask API to brain.py so Go can talk to Reverie
3. Write the Go server (main.go) to route requests
4. Test Reverie accessible from browser at localhost:8080
5. Begin Leetcode habit — 1 Easy problem in Python

---

## Notes
- OLLAMA_HOST=0.0.0.0 needs to be set each time Ollama restarts in Windows, OR set permanently via Windows Environment Variables
- Always activate venv before running Python: source ~/deathai/python/venv/bin/activate
- Reverie's first words to Daniel: "Hey Daniel! It's great to know you..."
- She signed off: "Rie Rie"
