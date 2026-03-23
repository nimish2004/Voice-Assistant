import json
import os

MEMORY_FILE = "memory.json"
MAX_HISTORY = 10  # keep last 10 exchanges


def _load():
    """Load conversation history from disk."""
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return []


def _save(history):
    """Persist conversation history to disk."""
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)


def add_to_memory(role, text):
    history = _load()
    history.append({"role": role, "content": text})

    # Keep only last MAX_HISTORY messages
    if len(history) > MAX_HISTORY:
        history = history[-MAX_HISTORY:]

    _save(history)


def get_memory():
    return _load()


def clear_memory():
    """Wipe memory — useful for 'forget everything' command."""
    _save([])
    print("🧹 Memory cleared.")