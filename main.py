from pydoc import text
from unittest import result

from wakeword import start_wake_engine
from speech import listen_and_transcribe
from llm_brain import get_intent_llm
from actions import handle_intent
import time
from state import RUNNING
from tts import speak


print("=================================")
print("  Personal Voice Assistant v2.0 ")
print("=================================")
speak("Welcome to Numa -your personal voice assistant. Say Numa to wake the system.")
print("Say 'Alexa' to wake.")
print("Press Ctrl+C to stop.\n")


# last_command_time = 0
# COMMAND_COOLDOWN = 4  # seconds

def on_wake():
    # global last_command_time
    # now = time.time()

    # # Cooldown to avoid double triggers
    # if now - last_command_time < COMMAND_COOLDOWN:
    #     return

    # last_command_time = now

    # Step 1: Listen
    text = listen_and_transcribe()
    if not text or len(text.split()) < 2:
       print("⚠️ Ignoring short / weak command")
       return

    print("User said:", text)

    # Step 2: Think (LLM)
    result = get_intent_llm(text)
    print("LLM result:", result)

    # Step 3: Act
    # Step 3: Act
    if "intents" in result:
        for single_intent in result["intents"]:
            print("Executing:", single_intent)
            handle_intent({"intent": single_intent})
    else:
        print("Executing:", result.get("intent"))
        handle_intent(result)

# Start system
start_wake_engine(on_wake)
