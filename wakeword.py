"""
wakeword.py — Listens 24/7 for the wake word and fires the callback.

Key improvements over v1:
  - Uses state module's proper API (state.is_running / state.set_processing)
  - Processing lock prevents overlapping wake events
  - Clean thread naming for easier debugging
  - Config block grouped at top for easy tuning
"""

import threading
import time

import numpy as np
import sounddevice as sd
from openwakeword.model import Model

import state
import tts as _tts             # interrupt playback on wake


# ── Config ────────────────────────────────────────────────────────────────────

WAKE_WORD       = "alexa"
THRESHOLD       = 0.8       # confidence score (0-1) to accept a detection
REQUIRED_HITS   = 3         # consecutive frames above threshold before firing
COOLDOWN        = 3.0       # seconds to ignore further detections after trigger
SAMPLE_RATE     = 16000
BLOCK_SIZE      = 1280


# ── Model ─────────────────────────────────────────────────────────────────────

print("🔄  Loading wake word model...")
_wake_model = Model(wakeword_models=[WAKE_WORD], inference_framework="onnx")
print("✅  Wake word model ready.")


# ── Internal state ─────────────────────────────────────────────────────────────

_last_trigger_time = 0.0
_hit_count         = 0


# ── Core engine ───────────────────────────────────────────────────────────────

def start_wake_engine(on_wake_callback):
    """
    Block the calling thread, streaming mic audio and firing on_wake_callback
    in a daemon thread whenever the wake word is confidently detected.

    The callback is never fired while a previous invocation is still running
    (state.is_processing() guard). This prevents audio chaos if the user
    triggers the wake word mid-sentence.
    """
    global _last_trigger_time, _hit_count

    def _audio_callback(indata, frames, time_info, status):
        global _last_trigger_time, _hit_count

        audio      = np.frombuffer(indata, dtype=np.int16)
        prediction = _wake_model.predict(audio)
        now        = time.time()
        score      = prediction.get(WAKE_WORD, 0)

        # Accumulate or reset consecutive hit counter
        if score > THRESHOLD:
            _hit_count += 1
        else:
            _hit_count = 0

        # Fire only when:
        #   1. Enough consecutive hits
        #   2. Cooldown elapsed since last trigger
        #   3. Not already processing a previous command
        if (
            _hit_count >= REQUIRED_HITS
            and (now - _last_trigger_time) > COOLDOWN
            and not state.is_processing()
        ):
            _last_trigger_time = now
            _hit_count         = 0

            # Stop Numa mid-speech — user is already giving next command
            _tts.interrupt()

            # Mark as processing BEFORE spawning thread to prevent race
            state.set_processing(True)
            print("\n🔥  Wake word detected!")

            t = threading.Thread(
                target=on_wake_callback,
                name="WakeHandler",
                daemon=True,
            )
            t.start()

    print("👂  Listening for wake word...")

    try:
        with sd.RawInputStream(
            samplerate=SAMPLE_RATE,
            blocksize=BLOCK_SIZE,
            dtype="int16",
            channels=1,
            callback=_audio_callback,
        ):
            while state.is_running():
                time.sleep(0.1)

    except KeyboardInterrupt:
        pass  # let main.py handle the shutdown message

    except Exception as e:
        print(f"❌  Wake engine error: {e}")