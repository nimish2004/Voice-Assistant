import requests
import json
import re
from memory import add_to_memory, get_memory

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "phi3"

# Short, fast prompt (less tokens = faster)
SYSTEM_PROMPT = """
You are Numa, the brain of a voice assistant.

Decide whether the user wants to:
1) Execute a system task
2) Have a conversation

If it is a task return ONLY compact JSON (no extra text):
{"type":"task","intent":"intent_name","parameters":{}}

If it is conversation return ONLY compact JSON:
{"type":"chat","response":"your reply"}

Available task intents (use EXACT names):

open_chrome, open_spotify, open_vscode, open_notepad, open_youtube
open_app       -> use parameters: {"app": "app_name"}
play_music, pause_music, next_track, prev_track
lock_laptop, shutdown, restart, sleep
mute, volume_up, volume_down
set_volume     -> use parameters: {"value": 0-100}
take_screenshot
tell_time, tell_date, battery_status
open_terminal, git_status
web_search     -> use parameters: {"query": "search terms"}
get_weather    -> use parameters: {"city": "city name"}
exit

If unclear: {"type":"chat","response":"Sorry, I didn't understand that."}
"""


def extract_json(text):
    """Safely extract JSON from model output."""
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except:
            pass
    
    # safe fallback
    return {
        "type": "chat",
        "response": "Sorry, I didn't understand that."
    }


def get_intent_llm(text):
    history = get_memory()

    conversation = ""

    for msg in history:
        conversation += f"{msg['role']}: {msg['content']}\n"

    conversation += f"user: {text}\nassistant:"

    payload = {
        "model": MODEL,
        "prompt": SYSTEM_PROMPT + "\n\n" + conversation,
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0,
            "num_predict": 80
        }
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=10)
        result = extract_json(response.json().get("response", ""))

        # Save to memory BEFORE returning (was broken before - dead code after return)
        add_to_memory("user", text)
        if result.get("type") == "chat":
            add_to_memory("assistant", result.get("response", ""))

        return result

    except requests.exceptions.ConnectionError:
        print("⚠️  Ollama server is not running. Start it with: ollama serve")
        return {
            "type": "chat",
            "response": "I can't think right now. Please make sure Ollama is running."
        }
    except Exception as e:
        print("LLM error:", e)
        return {
            "type": "chat",
            "response": "Something went wrong."
        }