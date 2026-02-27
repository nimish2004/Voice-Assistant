import requests
import json
import re

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "phi3"

# Short, fast prompt (less tokens = faster)
SYSTEM_PROMPT = """
Convert the user command into a JSON intent.

Valid intents:
open_chrome, open_spotify, open_vscode, open_notepad, set_volume,
open_youtube, play_music, pause_music, next_track,
prev_track, lock_laptop, shutdown, restart, sleep,
mute, volume_up, volume_down, take_screenshot,
tell_time, tell_date, battery_status, open_terminal,
git_status, exit.

If multiple:
{"intents":["intent1","intent2"]}

If single:
{"intent":"intent_name"}

If unknown:
{"intent":"unknown"}

Return JSON only.
"""


def extract_json(text):
    """Safely extract JSON from model output."""
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except:
            pass
    return {"intent": "unknown"}


def get_intent_llm(text):
    payload = {
        "model": MODEL,
        "prompt": SYSTEM_PROMPT + "\nUser: " + text,
        "stream": False,
        "format": "json",  # force JSON output
        "options": {
            "temperature": 0,
            "num_predict": 40
        }
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload)
        result = response.json().get("response", "")
        return extract_json(result)

    except Exception as e:
        print("LLM error:", e)
        return {"intent": "unknown"}