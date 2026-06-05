import requests
import sys
import os
from flask import Flask, request, jsonify
from flask_cors import CORS

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))
from config.reverie import SYSTEM_PROMPT, DEFAULT_MODEL, OLLAMA_URL

CHAT_URL = f"{OLLAMA_URL}/api/chat"

app = Flask(__name__)
CORS(app)

conversation_history = []

def ask(prompt, model=DEFAULT_MODEL):
    conversation_history.append({
        "role": "user",
        "content": prompt
    })
    payload = {
        "model": model,
        "messages": [{"role": "system", "content": SYSTEM_PROMPT}] + conversation_history,
        "stream": False
    }
    try:
        response = requests.post(CHAT_URL, json=payload, timeout=120)
        data = response.json()
        reply = data["message"]["content"]
        conversation_history.append({
            "role": "assistant",
            "content": reply
        })
        return reply
    except Exception as e:
        return f"Reverie is unreachable: {e}"

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

@app.route('/reset', methods=['POST'])
def reset():
    global conversation_history
    conversation_history = []
    return jsonify({'status': 'Memory cleared'})

if __name__ == "__main__":
    print("Reverie API online at http://0.0.0.0:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)
