import requests
import json
import re

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "phi3"

# Short, fast prompt (less tokens = faster)
SYSTEM_PROMPT = """
You are the brain of a voice assistant.

Decide whether the user wants to:

1) Execute a system task
2) Have a conversation

If it is a task return JSON:

{
"type":"task",
"intent":"intent_name",
"parameters":{}
}

If it is conversation return JSON:

{
"type":"chat",
"response":"assistant reply"
}

Available task intents:

open_chrome
open_spotify
open_vscode
open_notepad
open_youtube
play_music
pause_music
next_track
prev_track
lock_laptop
shutdown
restart
sleep
mute
volume_up
volume_down
set_volume
take_screenshot
tell_time
tell_date
battery_status
open_terminal
git_status
exit

If the sentence is unclear return:

{
"type":"chat",
"response":"Sorry, I didn't understand that."
}
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
    payload = {
        "model": MODEL,
        "prompt": SYSTEM_PROMPT + "\nUser: " + text,
        "stream": False,
        "format": "json",  # force JSON output
        "options": {
            "temperature": 0,
            "num_predict": 60
        }
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload)
        result = response.json().get("response", "")
        return extract_json(result)

    except Exception as e:
        print("LLM error:", e)
        return {
            "type": "chat",
            "response": "Something went wrong."
        }