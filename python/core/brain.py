import sys
import os
import re
import json
import requests
from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from functools import wraps

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../"))
from config.reverie import SYSTEM_PROMPT, DEFAULT_MODEL, OLLAMA_URL
from tools.system_tools import TOOLS, TOOL_DEFINITIONS
from tools.semantic_memory import get_relevant_memories

# ─── Config ───────────────────────────────────────────────────────────────────

CHAT_URL = f"{OLLAMA_URL}/api/chat"
DB_PATH = os.path.join(os.path.dirname(__file__), "../../data/reverie.db")
MAX_PROMPT_CHARS = 12000
MAX_CLIENT_CONTEXT_CHARS = 600
HISTORY_SEARCH_LIMIT = 200
MODEL_HISTORY_MAX_MESSAGES = int(os.getenv("MODEL_HISTORY_MAX_MESSAGES", "80"))
MODEL_HISTORY_MAX_CHARS = int(os.getenv("MODEL_HISTORY_MAX_CHARS", "16000"))
ACCESS_KEY = os.getenv("DEATHAI_ACCESS_KEY", "").strip()
VALID_MODEL_PATTERN = re.compile(r"^[A-Za-z0-9_.:-]{1,80}$")
TOOL_ROUTER_MODEL = "llama3.2:1b"

# ─── Flask + DB ───────────────────────────────────────────────────────────────

app = Flask(__name__)
CORS(app)
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(20), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()

# ─── Auth ─────────────────────────────────────────────────────────────────────

def require_access_key(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not ACCESS_KEY:
            return func(*args, **kwargs)
        provided = request.headers.get("X-DeathAI-Key", "").strip()
        if provided != ACCESS_KEY:
            return jsonify({"error": "Unauthorized"}), 401
        return func(*args, **kwargs)
    return wrapper

# ─── Memory ───────────────────────────────────────────────────────────────────

def get_all_history():
    messages = (
        Message.query
        .order_by(Message.timestamp.desc(), Message.id.desc())
        .limit(MODEL_HISTORY_MAX_MESSAGES)
        .all()
    )
    messages.reverse()
    trimmed = []
    total_chars = 0
    for message in reversed(messages):
        content_length = len(message.content or "")
        if trimmed and total_chars + content_length > MODEL_HISTORY_MAX_CHARS:
            break
        trimmed.append(message)
        total_chars += content_length
    trimmed.reverse()
    return [{"role": m.role, "content": m.content} for m in trimmed]

def get_history_records(search=""):
    query = Message.query
    search = str(search or "").strip()
    if search:
        pattern = f"%{search}%"
        query = query.filter(Message.content.ilike(pattern))
    messages = (
        query
        .order_by(Message.timestamp.desc(), Message.id.desc())
        .limit(HISTORY_SEARCH_LIMIT)
        .all()
    )
    return [
        {
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "timestamp": m.timestamp.isoformat() + "Z"
        }
        for m in messages
    ]

def save_message(role, content):
    if role not in {"user", "assistant"}:
        raise ValueError("Invalid message role")
    msg = Message(role=role, content=content)
    db.session.add(msg)
    db.session.commit()
    return msg

def build_client_context_message(client_context):
    context = str(client_context or "").strip()
    if not context:
        return []
    context = context[:MAX_CLIENT_CONTEXT_CHARS]
    return [{
        "role": "system",
        "content": (
            "Current local UI presence hint. Not saved memory. "
            "Tune pacing only: ask a follow-up sometimes when user is active, "
            f"don't push when idle. Hint: {context}"
        )
    }]

# ─── Tools ────────────────────────────────────────────────────────────────────

def call_tool(tool_name, params):
    """Execute a tool by name with given params"""
    if tool_name not in TOOLS:
        return f"Unknown tool: {tool_name}"
    try:
        return TOOLS[tool_name](**params)
    except Exception as e:
        return f"Tool error: {e}"

def detect_tool_intent(prompt):
    """
    Use llama3.2:1b (fast/small) to detect if a tool should be called.
    Returns (tool_name, params) or (None, None).
    """
    system = (
        "You are a tool router. If a computer action is needed output ONLY JSON. "
        "If no tool needed output ONLY: NONE\n\n"
        "Examples:\n"
        "- open youtube -> {\"tool\": \"open_url\", \"params\": {\"url\": \"https://youtube.com\"}}\n"
        "- open mumblechat.online -> {\"tool\": \"open_url\", \"params\": {\"url\": \"https://mumblechat.online\"}}\n"
        "- search youtube for X -> {\"tool\": \"open_url\", \"params\": {\"url\": \"https://youtube.com/results?search_query=X\"}}\n"
        "- search google for X -> {\"tool\": \"open_url\", \"params\": {\"url\": \"https://google.com/search?q=X\"}}\n"
        "- list files in deathai -> {\"tool\": \"list_files\", \"params\": {\"path\": \"~/deathai\"}}\n"
        "- create folder music -> {\"tool\": \"create_folder\", \"params\": {\"path\": \"~/music\"}}\n"
        "- search web for X -> {\"tool\": \"web_search\", \"params\": {\"query\": \"X\"}}\n"
        "Replace X with the actual search terms from the user message. "
        "For YouTube searches encode spaces as + in the URL."
    )

    try:
        response = requests.post(CHAT_URL, json={
            "model": TOOL_ROUTER_MODEL,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt}
            ],
            "stream": False
        }, timeout=15)
        response.raise_for_status()
        reply = response.json()["message"]["content"].strip()

        if reply.upper() == "NONE" or not reply.startswith("{"):
            return None, None

        data = json.loads(reply)
        tool_name = data.get("tool") or data.get("tool_call")
        params = data.get("params", {})

        if tool_name and tool_name in TOOLS:
            return tool_name, params

    except Exception:
        pass

    return None, None

# ─── Core ask function ────────────────────────────────────────────────────────

def ask(prompt, model=DEFAULT_MODEL, client_context=None):
    """
    Main ask function:
    1. Save user message
    2. Check for tool intent via llama3.2:1b
    3. If tool needed — run it, feed result to dolphin3 for natural response
    4. If no tool — use semantic search to find relevant memories
    5. Send focused context to dolphin3
    """
    save_message("user", prompt)

    # Step 1: Check for tool intent
    tool_name, params = detect_tool_intent(prompt)

    if tool_name:
        # Run the tool
        tool_result = call_tool(tool_name, params)

        # Ask dolphin3 to respond naturally about what was done
        follow_up_payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"You just ran the '{tool_name}' tool for me. The result was: {tool_result}. Tell me what you did in your own voice, briefly and naturally."}
            ],
            "stream": False
        }
        try:
            resp = requests.post(CHAT_URL, json=follow_up_payload, timeout=60)
            resp.raise_for_status()
            reply = resp.json()["message"]["content"]
            save_message("assistant", reply)
            return reply
        except Exception as e:
            # Fallback — just confirm the tool ran
            reply = f"Done — {tool_result}"
            save_message("assistant", reply)
            return reply

    # Step 2: No tool needed — use semantic memory for focused context
    all_history = get_all_history()
    relevant = get_relevant_memories(prompt, all_history, top_k=6)

    payload = {
        "model": model,
        "messages": (
            [{"role": "system", "content": SYSTEM_PROMPT}]
            + build_client_context_message(client_context)
            + relevant
            + [{"role": "user", "content": prompt}]
        ),
        "stream": False
    }

    try:
        response = requests.post(CHAT_URL, json=payload, timeout=120)
        response.raise_for_status()
        reply = response.json()["message"]["content"]
        save_message("assistant", reply)
        return reply
    except Exception as e:
        return f"Reverie is unreachable: {e}"

# ─── Routes ───────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return send_file(os.path.join(os.path.dirname(__file__), "chat.html"))

@app.route("/assets/<path:filename>", methods=["GET"])
def assets(filename):
    return send_from_directory(
        os.path.join(os.path.dirname(__file__), "assets"), filename
    )

@app.route("/reve-animations/<path:filename>", methods=["GET"])
def reve_animations(filename):
    return send_from_directory(
        os.path.join(os.path.dirname(__file__), "../../reve animations"), filename
    )

@app.route("/ask", methods=["POST"])
@require_access_key
def ask_endpoint():
    data = request.get_json(silent=True) or {}
    prompt = str(data.get("prompt", "")).strip()
    model = str(data.get("model", DEFAULT_MODEL)).strip()
    client_context = str(data.get("client_context", "")).strip()

    if not prompt:
        return jsonify({"error": "No prompt provided"}), 400
    if len(prompt) > MAX_PROMPT_CHARS:
        return jsonify({"error": f"Prompt too long (max {MAX_PROMPT_CHARS} chars)"}), 413
    if not VALID_MODEL_PATTERN.fullmatch(model):
        return jsonify({"error": "Invalid model name"}), 400

    reply = ask(prompt, model, client_context)
    return jsonify({"reply": reply})

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "Reverie is online",
        "tool_router": TOOL_ROUTER_MODEL,
        "conversation_model": DEFAULT_MODEL,
        "auth_required": bool(ACCESS_KEY),
    })

@app.route("/history", methods=["GET"])
@require_access_key
def history():
    messages = get_history_records(request.args.get("q", ""))
    return jsonify({"messages": messages})

@app.route("/history/<int:message_id>", methods=["DELETE"])
@require_access_key
def delete_history_message(message_id):
    message = db.session.get(Message, message_id)
    if message is None:
        return jsonify({"error": "Message not found"}), 404
    db.session.delete(message)
    db.session.commit()
    return jsonify({"status": "Message deleted", "id": message_id})

@app.route("/reset", methods=["POST"])
@require_access_key
def reset():
    Message.query.delete()
    db.session.commit()
    return jsonify({"status": "Memory cleared"})

# ─── Run ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Reverie API online at http://0.0.0.0:5000")
    print(f"Tool router: {TOOL_ROUTER_MODEL}")
    print(f"Conversation model: {DEFAULT_MODEL}")
    app.run(host="0.0.0.0", port=5000, debug=False)
