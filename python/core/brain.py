import sys
import os
import re
import requests
from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))
from config.reverie import SYSTEM_PROMPT, DEFAULT_MODEL, OLLAMA_URL

CHAT_URL = f"{OLLAMA_URL}/api/chat"
DB_PATH = os.path.join(os.path.dirname(__file__), '../../data/reverie.db')
MAX_PROMPT_CHARS = 12000
MAX_CLIENT_CONTEXT_CHARS = 600
VALID_MODEL_PATTERN = re.compile(r"^[A-Za-z0-9_.:-]{1,80}$")

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_PATH}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(20), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()

def get_model_history():
    messages = Message.query.order_by(Message.timestamp).all()
    return [{"role": m.role, "content": m.content} for m in messages]

def get_history_records():
    messages = Message.query.order_by(Message.timestamp, Message.id).all()
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

def build_transient_context(client_context):
    context = str(client_context or '').strip()
    if not context:
        return []
    context = context[:MAX_CLIENT_CONTEXT_CHARS]
    return [{
        "role": "system",
        "content": (
            "Current local UI presence hint. This is not saved memory. "
            "Use it only to tune pacing: ask a short follow-up question sometimes "
            "when the user is actively engaged; do not ask questions when the hint "
            f"says they appear idle. Hint: {context}"
        )
    }]

def ask(prompt, model=DEFAULT_MODEL, client_context=None):
    save_message("user", prompt)
    history = get_model_history()
    payload = {
        "model": model,
        "messages": (
            [{"role": "system", "content": SYSTEM_PROMPT}]
            + build_transient_context(client_context)
            + history
        ),
        "stream": False
    }
    try:
        response = requests.post(CHAT_URL, json=payload, timeout=120)
        response.raise_for_status()
        data = response.json()
        reply = data["message"]["content"]
        save_message("assistant", reply)
        return reply
    except Exception as e:
        return f"Reverie is unreachable: {e}"

@app.route('/')
def index():
    return send_file(os.path.join(os.path.dirname(__file__), 'chat.html'))

@app.route('/assets/<path:filename>', methods=['GET'])
def assets(filename):
    return send_from_directory(os.path.join(os.path.dirname(__file__), 'assets'), filename)

@app.route('/reve-animations/<path:filename>', methods=['GET'])
def reve_animations(filename):
    return send_from_directory(os.path.join(os.path.dirname(__file__), '../../reve animations'), filename)

@app.route('/ask', methods=['POST'])
def ask_endpoint():
    data = request.get_json(silent=True) or {}
    prompt = str(data.get('prompt', '')).strip()
    model = str(data.get('model', DEFAULT_MODEL)).strip()
    client_context = str(data.get('client_context', '')).strip()
    if not prompt:
        return jsonify({'error': 'No prompt provided'}), 400
    if len(prompt) > MAX_PROMPT_CHARS:
        return jsonify({'error': f'Prompt exceeds {MAX_PROMPT_CHARS} characters'}), 413
    if not VALID_MODEL_PATTERN.fullmatch(model):
        return jsonify({'error': 'Invalid model name'}), 400
    reply = ask(prompt, model, client_context)
    return jsonify({'reply': reply})

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'Reverie is online'})

@app.route('/history', methods=['GET'])
def history():
    messages = get_history_records()
    return jsonify({'messages': messages})

@app.route('/history/<int:message_id>', methods=['DELETE'])
def delete_history_message(message_id):
    message = Message.query.get(message_id)
    if message is None:
        return jsonify({'error': 'Message not found'}), 404
    db.session.delete(message)
    db.session.commit()
    return jsonify({'status': 'Message deleted', 'id': message_id})

@app.route('/reset', methods=['POST'])
def reset():
    Message.query.delete()
    db.session.commit()
    return jsonify({'status': 'Memory cleared'})

if __name__ == "__main__":
    print("Reverie API online at http://0.0.0.0:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)
