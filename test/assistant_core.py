from openwakeword.model import Model
import sounddevice as sd
import numpy as np
import time
import winsound
import whisper
import scipy.io.wavfile as wav
import os
import pyautogui
import datetime

# ---------- LOAD MODELS ----------
wake_model = Model(wakeword_models=["alexa"], inference_framework="onnx")
whisper_model = whisper.load_model("base")

sample_rate = 16000
block_size = 1280

last_trigger_time = 0
COOLDOWN = 3.0

print("Assistant started.")
print("Say 'Alexa' to wake.")
print("Press Ctrl+C to exit.\n")

# ---------- BRAIN ----------
def get_intent(text):
    text = text.lower()

    if "play" in text and "music" in text:
        return "play_music"

    elif "pause" in text or "stop" in text:
        return "pause_music"

    elif "open" in text and "chrome" in text:
        return "open_chrome"

    elif "time" in text:
        return "tell_time"

    elif "exit" in text or "quit" in text:
        return "exit"

    else:
        return "unknown"

# ---------- ACTION ENGINE ----------
def handle_intent(intent):
    if intent == "play_music":
        print("Action: Playing music")
        pyautogui.press("playpause")

    elif intent == "pause_music":
        print("Action: Pausing music")
        pyautogui.press("playpause")

    elif intent == "open_chrome":
        print("Action: Opening Chrome")
        os.system("start chrome")

    elif intent == "tell_time":
        now = datetime.datetime.now().strftime("%H:%M")
        print("Time is:", now)

    elif intent == "exit":
        print("Goodbye!")
        os._exit(0)

    else:
        print("I don't understand that yet.")

# ---------- RECORD + TRANSCRIBE ----------
def record_and_transcribe():
    print("🎤 Listening for command...")
    winsound.Beep(800, 150)

    seconds = 4
    recording = sd.rec(int(seconds * sample_rate),
                        samplerate=sample_rate,
                        channels=1,
                        dtype="int16")
    sd.wait()

    wav.write("command.wav", sample_rate, recording)

    print("🧠 Transcribing...")
    result = whisper_model.transcribe("command.wav")
    text = result["text"].strip().lower()

    print("You said:", text)
    winsound.Beep(1200, 150)

    intent = get_intent(text)
    print("Intent:", intent)
    handle_intent(intent)

# ---------- WAKE WORD LOGIC ----------
hit_count = 0
REQUIRED_HITS = 3

def callback(indata, frames, time_info, status):
    global last_trigger_time, hit_count
    audio = np.frombuffer(indata, dtype=np.int16)
    prediction = wake_model.predict(audio)

    now = time.time()

    if prediction["alexa"] > 0.85:
        hit_count += 1
    else:
        hit_count = 0

    if hit_count >= REQUIRED_HITS:
        if now - last_trigger_time > COOLDOWN:
            last_trigger_time = now
            hit_count = 0
            print("\n🔥 Wake word detected!")
            time.sleep(0.3)
            record_and_transcribe()

# ---------- MAIN LOOP ----------
try:
    with sd.RawInputStream(
        samplerate=sample_rate,
        blocksize=block_size,
        dtype="int16",
        channels=1,
        callback=callback
    ):
        while True:
            time.sleep(0.1)

except KeyboardInterrupt:
    print("\nAssistant stopped.")
