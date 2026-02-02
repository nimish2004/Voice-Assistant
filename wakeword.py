import state
from openwakeword.model import Model
import sounddevice as sd
import numpy as np
import time

# ---------- CONFIG ----------
WAKE_WORD = "alexa"
THRESHOLD = 0.85
REQUIRED_HITS = 3
COOLDOWN = 3.0

# ---------- MODEL ----------
wake_model = Model(wakeword_models=[WAKE_WORD], inference_framework="onnx")

sample_rate = 16000
block_size = 1280

last_trigger_time = 0
hit_count = 0


# ---------- CORE FUNCTION ----------
def start_wake_engine(on_wake_callback):
    global last_trigger_time, hit_count

    def callback(indata, frames, time_info, status):
        global last_trigger_time, hit_count

        audio = np.frombuffer(indata, dtype=np.int16)
        prediction = wake_model.predict(audio)

        now = time.time()

        if prediction[WAKE_WORD] > THRESHOLD:
            hit_count += 1
        else:
            hit_count = 0

        if hit_count >= REQUIRED_HITS:
            if now - last_trigger_time > COOLDOWN:
                last_trigger_time = now
                hit_count = 0
                print("🔥 Wake word detected!")
                on_wake_callback()

    try:
        with sd.RawInputStream(
            samplerate=sample_rate,
            blocksize=block_size,
            dtype="int16",
            channels=1,
            callback=callback
        ):
            while state.RUNNING:
                time.sleep(0.1)

    except KeyboardInterrupt:
        print("\nWake engine stopped.")
