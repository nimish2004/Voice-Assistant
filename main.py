from wakeword import start_wake_engine
from speech import listen_and_transcribe
from brain import get_intent
from actions import handle_intent

print("=================================")
print("  Personal Voice Assistant v1.0 ")
print("=================================")
print("Say 'Alexa' to wake.")
print("Press Ctrl+C to stop.\n")

def on_wake():
    # Step 1: Listen
    text = listen_and_transcribe()

    # Step 2: Think
    intent = get_intent(text)
    print("Intent detected:", intent)

    # Step 3: Act
    handle_intent(intent)

# Start system
start_wake_engine(on_wake)
