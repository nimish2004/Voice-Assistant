import os
import json
import re
from google import genai
from google.genai import types
from dotenv import load_dotenv
from memory import add_to_memory, get_memory

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("⚠️ GEMINI_API_KEY not found in .env file!")

client = genai.Client(api_key=GEMINI_API_KEY)

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
clear_memory
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

    return {
        "type": "chat",
        "response": "Sorry, I didn't understand that."
    }


def get_intent_llm(text):
    if not GEMINI_API_KEY:
        return {
            "type": "chat",
            "response": "Please set your Gemini API key in the .env file."
        }

    history = get_memory()
    conversation = ""

    for msg in history:
        conversation += f"{msg['role']}: {msg['content']}\n"

    conversation += f"user: {text}\nassistant:"
    full_prompt = SYSTEM_PROMPT + "\n\n" + conversation

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=full_prompt,
            config=types.GenerateContentConfig(
                temperature=0,
                response_mime_type="application/json",
            ),
        )

        result = extract_json(response.text)

        add_to_memory("user", text)
        if result.get("type") == "chat":
            add_to_memory("assistant", result.get("response", ""))

        return result

    except Exception as e:
        print("LLM error:", e)
        return {
            "type": "chat",
            "response": "Something went wrong communicating with the cloud AI."
        }
