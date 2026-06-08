import requests
import numpy as np
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))
from config.reverie import OLLAMA_URL

EMBED_URL = f"{OLLAMA_URL}/api/embeddings"
EMBED_MODEL = "nomic-embed-text"

def get_embedding(text):
    """Convert text to a vector using nomic-embed-text"""
    try:
        response = requests.post(EMBED_URL, json={
            "model": EMBED_MODEL,
            "prompt": text[:2000]
        }, timeout=30)
        response.raise_for_status()
        return np.array(response.json()["embedding"])
    except Exception as e:
        return None

def cosine_similarity(a, b):
    """Calculate similarity between two vectors — 1.0 = identical, 0.0 = unrelated"""
    if a is None or b is None:
        return 0.0
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def get_relevant_memories(prompt, messages, top_k=6):
    """Find the most relevant memories for a given prompt"""
    if not messages:
        return []

    prompt_embedding = get_embedding(prompt)
    if prompt_embedding is None:
        return messages[-top_k:]

    scored = []
    for msg in messages:
        content = msg.get("content", "")
        if not content:
            continue
        msg_embedding = get_embedding(content)
        score = cosine_similarity(prompt_embedding, msg_embedding)
        scored.append((score, msg))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = [msg for _, msg in scored[:top_k]]

    return top

def build_focused_prompt(prompt, relevant_memories, tool_definitions=""):
    """Build a tight focused prompt instead of dumping everything"""
    memory_text = ""
    if relevant_memories:
        memory_text = "\n\nRELEVANT CONTEXT FROM MEMORY:\n"
        for msg in relevant_memories:
            role = msg.get("role", "unknown").upper()
            content = msg.get("content", "")[:300]
            memory_text += f"{role}: {content}\n"

    tool_text = ""
    if tool_definitions:
        tool_text = f"\n\nTOOLS:\n{tool_definitions}"

    return memory_text + tool_text
