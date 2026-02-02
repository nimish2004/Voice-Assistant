import requests
import json

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "mistral"

SYSTEM_PROMPT = """
You are an AI brain for a voice assistant.

Your job is to convert user text into structured intents.

Only respond in JSON.

Valid intents:
- open_chrome
- open_spotify
- open_vscode
- open_notepad
- open_youtube
- play_music
- pause_music
- next_track
- prev_track
- lock_laptop
- shutdown
- restart
- sleep
- mute
- volume_up
- volume_down
- take_screenshot
- tell_time
- tell_date
- battery_status
- open_terminal
- git_status
- exit

If multiple actions are needed, return:

{
  "intents": ["intent1", "intent2"]
}

If only one action:

{
  "intent": "intent_name"
}

If you cannot map it, return:

{
  "intent": "unknown"
}
"""

def get_intent_llm(text):
    payload = {
        "model": MODEL,
        "prompt": SYSTEM_PROMPT + "\nUser: " + text,
        "stream": False
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload)
        result = response.json()["response"]

        data = json.loads(result)
        return data

    except Exception as e:
        print("LLM error:", e)
        return {"intent": "unknown"}
