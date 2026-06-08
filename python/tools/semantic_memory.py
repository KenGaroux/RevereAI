import requests
import numpy as np
import os
import sys
import turbovec

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))
from config.reverie import OLLAMA_URL

EMBED_URL = f"{OLLAMA_URL}/api/embeddings"
EMBED_MODEL = "nomic-embed-text"

def get_embedding(text):
    """Convert text to a 768-dim vector using nomic-embed-text"""
    try:
        response = requests.post(EMBED_URL, json={
            "model": EMBED_MODEL,
            "prompt": str(text)[:2000]
        }, timeout=30)
        response.raise_for_status()
        return np.array(response.json()["embedding"], dtype=np.float32)
    except Exception:
        return None

def get_relevant_memories(prompt, messages, top_k=6):
    """
    Find the most semantically relevant memories for a given prompt.
    Uses turbovec TurboQuantIndex for fast vector search.
    Falls back to most recent messages if embedding fails.
    """
    if not messages:
        return []

    if len(messages) <= top_k:
        return messages

    # Embed all messages
    embeddings = []
    valid_messages = []
    for msg in messages:
        content = msg.get("content", "")
        if not content:
            continue
        emb = get_embedding(content)
        if emb is not None:
            embeddings.append(emb)
            valid_messages.append(msg)

    if not embeddings:
        return messages[-top_k:]

    # Embed the prompt
    prompt_emb = get_embedding(prompt)
    if prompt_emb is None:
        return messages[-top_k:]

    # Build turbovec index
    try:
        matrix = np.stack(embeddings)
        index = turbovec.TurboQuantIndex(dim=768)
        index.add(matrix)
        index.prepare()

        query = prompt_emb.reshape(1, -1)
        k = min(top_k, len(valid_messages))
        scores, indices = index.search(query, k=k)

        # Return messages sorted by relevance
        top_indices = indices[0].tolist()
        return [valid_messages[i] for i in top_indices if i < len(valid_messages)]

    except Exception:
        # Fallback to most recent
        return valid_messages[-top_k:]
