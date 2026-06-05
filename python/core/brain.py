import requests
import sys
import os
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))
from config.reverie import SYSTEM_PROMPT, DEFAULT_MODEL, OLLAMA_URL

CHAT_URL = f"{OLLAMA_URL}/api/chat"
DB_PATH = os.path.join(os.path.dirname(__file__), '../../data/reverie.db')

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

def get_history():
    messages = Message.query.order_by(Message.timestamp).all()
    return [{"role": m.role, "content": m.content} for m in messages]

def save_message(role, content):
    msg = Message(role=role, content=content)
    db.session.add(msg)
    db.session.commit()

def ask(prompt, model=DEFAULT_MODEL):
    save_message("user", prompt)
    history = get_history()
    payload = {
        "model": model,
        "messages": [{"role": "system", "content": SYSTEM_PROMPT}] + history,
        "stream": False
    }
    try:
        response = requests.post(CHAT_URL, json=payload, timeout=120)
        data = response.json()
        reply = data["message"]["content"]
        save_message("assistant", reply)
        return reply
    except Exception as e:
        return f"Reverie is unreachable: {e}"

@app.route('/')
def index():
    return send_file(os.path.join(os.path.dirname(__file__), 'chat.html'))

@app.route('/ask', methods=['POST'])
def ask_endpoint():
    data = request.json
    prompt = data.get('prompt', '')
    model = data.get('model', DEFAULT_MODEL)
    if not prompt:
        return jsonify({'error': 'No prompt provided'}), 400
    reply = ask(prompt, model)
    return jsonify({'reply': reply})

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'Reverie is online'})

@app.route('/history', methods=['GET'])
def history():
    messages = get_history()
    return jsonify({'messages': messages})

@app.route('/reset', methods=['POST'])
def reset():
    Message.query.delete()
    db.session.commit()
    return jsonify({'status': 'Memory cleared'})

if __name__ == "__main__":
    print("Reverie API online at http://0.0.0.0:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)
