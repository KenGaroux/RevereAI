import requests
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))
from config.reverie import SYSTEM_PROMPT, DEFAULT_MODEL, OLLAMA_URL

CHAT_URL = f"{OLLAMA_URL}/api/chat"

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

if __name__ == "__main__":
    print("Reverie online. Type 'quit' to exit.")
    print("-" * 40)
    while True:
        user_input = input("You: ").strip()
        if not user_input:
            continue
        if user_input.lower() == "quit":
            print("Reve: Later.")
            break
        reply = ask(user_input)
        print(f"Reve: {reply}\n")
