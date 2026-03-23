from wakeword import start_wake_engine
from speech import listen_and_transcribe
from llm_brain import get_intent_llm
from actions import handle_intent
from state import RUNNING
from tts import speak


print("====================================")
print("   Numa - Personal Voice Assistant  ")
print("====================================")
print("[NOTE] Wake word is 'Alexa' (temporary, Numa model in training)")
print("Press Ctrl+C to stop.\n")
speak("Welcome! I am Numa, your personal voice assistant. Say Alexa to wake me up.")


def on_wake():
    try:
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
        if result.get("type") == "task":
            handle_intent(result)

        elif result.get("type") == "chat":
            reply = result.get("response", "")
            speak(reply)

        else:
            print("Unknown response type")

    except Exception as e:
        print(f"Error handling wake event: {e}")


# Start system
start_wake_engine(on_wake)
