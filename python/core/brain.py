import sys
import os
import re
import requests
from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from functools import wraps

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../'))
from tools.system_tools import TOOLS
from config.reverie import SYSTEM_PROMPT, DEFAULT_MODEL, OLLAMA_URL

CHAT_URL = f"{OLLAMA_URL}/api/chat"
DB_PATH = os.path.join(os.path.dirname(__file__), '../../data/reverie.db')
MAX_PROMPT_CHARS = 12000
MAX_CLIENT_CONTEXT_CHARS = 600
HISTORY_SEARCH_LIMIT = 200
MODEL_HISTORY_MAX_MESSAGES = int(os.getenv('MODEL_HISTORY_MAX_MESSAGES', '80'))
MODEL_HISTORY_MAX_CHARS = int(os.getenv('MODEL_HISTORY_MAX_CHARS', '16000'))
ACCESS_KEY = os.getenv('DEATHAI_ACCESS_KEY', '').strip()
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

def require_access_key(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not ACCESS_KEY:
            return func(*args, **kwargs)
        provided = request.headers.get('X-DeathAI-Key', '').strip()
        if provided != ACCESS_KEY:
            return jsonify({'error': 'Unauthorized'}), 401
        return func(*args, **kwargs)
    return wrapper

def get_model_history():
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
        content_length = len(message.content or '')
        if trimmed and total_chars + content_length > MODEL_HISTORY_MAX_CHARS:
            break
        trimmed.append(message)
        total_chars += content_length
    trimmed.reverse()
    return [{"role": m.role, "content": m.content} for m in trimmed]

def get_history_records(search=''):
    query = Message.query
    search = str(search or '').strip()
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

def detect_and_run_tool(prompt):
    """Check if prompt is a tool request and execute it"""
    prompt_lower = prompt.lower()
    
    # Open URL detection
    if any(word in prompt_lower for word in ['open ', 'go to ', 'browse to ', 'navigate to ']):
        import re
        urls = re.findall(r'(https?://[^\s]+|[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}[^\s]*)', prompt)
        if urls:
            return TOOLS['open_url']['function'](urls[0])
    
    # List files detection
    if any(word in prompt_lower for word in ['list files', 'show files', 'what files', 'ls ']):
        path = '~'
        if 'in ' in prompt_lower:
            parts = prompt_lower.split('in ')
            if len(parts) > 1:
                path = parts[-1].strip()
        return TOOLS['list_files']['function'](path)
    
    # Create folder detection
    if any(word in prompt_lower for word in ['create folder', 'make folder', 'mkdir', 'new folder']):
        words = prompt.split()
        if len(words) > 2:
            return TOOLS['create_folder']['function']('~/' + words[-1])
    
    return None


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
@require_access_key
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
    # Check if this is a tool request first
    tool_result = detect_and_run_tool(prompt)
    if tool_result:
        return jsonify({'reply': tool_result})
    
    reply = ask(prompt, model, client_context)
    return jsonify({'reply': reply})

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'Reverie is online',
        'auth_required': bool(ACCESS_KEY),
        'model_history_max_messages': MODEL_HISTORY_MAX_MESSAGES,
        'model_history_max_chars': MODEL_HISTORY_MAX_CHARS
    })

@app.route('/history', methods=['GET'])
@require_access_key
def history():
    messages = get_history_records(request.args.get('q', ''))
    return jsonify({'messages': messages})

@app.route('/history/<int:message_id>', methods=['DELETE'])
@require_access_key
def delete_history_message(message_id):
    message = db.session.get(Message, message_id)
    if message is None:
        return jsonify({'error': 'Message not found'}), 404
    db.session.delete(message)
    db.session.commit()
    return jsonify({'status': 'Message deleted', 'id': message_id})

@app.route('/reset', methods=['POST'])
@require_access_key
def reset():
    Message.query.delete()
    db.session.commit()
    return jsonify({'status': 'Memory cleared'})

if __name__ == "__main__":
    print("Reverie API online at http://0.0.0.0:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)
