from wakeword import start_wake_engine
from speech import listen_and_transcribe
from llm_brain import get_intent_llm
from actions import handle_intent
import time
from state import RUNNING


print("=================================")
print("  Personal Voice Assistant v2.0 ")
print("=================================")
print("Say 'Alexa' to wake.")
print("Press Ctrl+C to stop.\n")


last_command_time = 0
COMMAND_COOLDOWN = 4  # seconds

def on_wake():
    global last_command_time
    now = time.time()

    # Cooldown to avoid double triggers
    if now - last_command_time < COMMAND_COOLDOWN:
        return

    last_command_time = now

    # Step 1: Listen
    text = listen_and_transcribe()
    if not text:
        return

    print("User said:", text)

    # Step 2: Think (LLM)
    result = get_intent_llm(text)
    print("LLM result:", result)

    # Step 3: Act
    if "intents" in result:
        for intent in result["intents"]:
            print("Executing:", intent)
            handle_intent(intent)
    else:
        intent = result.get("intent", "unknown")
        print("Executing:", intent)
        handle_intent(intent)

# Start system
start_wake_engine(on_wake)
