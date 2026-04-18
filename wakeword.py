"""
wakeword.py - Listens 24/7 for the wake word and fires the callback.

Key behaviours:
  - Processing lock: never fires while a previous command is being handled.
  - Post-speech silence window: ignores wake detections for POST_SPEECH_SILENCE_SEC
    after Numa finishes speaking. This prevents Numa's own TTS voice from
    acoustically resembling the wake word and self-triggering. This is the
    fix for false 0.8s empty audio detections.
  - tts.interrupt() called on valid wake so Numa stops talking immediately
    when the user wants to give a new command.
"""

import threading
import time

import numpy as np
import sounddevice as sd
from openwakeword.model import Model

import state
import tts as _tts
from config.settings import settings


# ── Config ────────────────────────────────────────────────────────────────────

SAMPLE_RATE = 16000
BLOCK_SIZE  = 1280

# How long after Numa finishes speaking to ignore wake detections.
# Prevents Numa's own voice from triggering itself.
# 1.5s is enough for audio to fully clear the mic feedback path.
POST_SPEECH_SILENCE_SEC = 1.5

def _cfg(key: str):
    return settings.get(key)


# ── Model ─────────────────────────────────────────────────────────────────────

print("[Numa] Loading wake word model...")
_wake_model = Model(
    wakeword_models     = [settings.get("wake_word")],
    inference_framework = "onnx",
)
print("[Numa] Wake word model ready.")


# ── Internal state ────────────────────────────────────────────────────────────

_last_trigger_time = 0.0
_hit_count         = 0


# ── Core engine ───────────────────────────────────────────────────────────────

def start_wake_engine(on_wake_callback):
    """
    Block the calling thread, streaming mic audio and firing on_wake_callback
    in a daemon thread whenever the wake word is confidently detected.
    """
    global _last_trigger_time, _hit_count

    def _audio_callback(indata, frames, time_info, status):
        global _last_trigger_time, _hit_count

        audio     = np.frombuffer(indata, dtype=np.int16)
        prediction= _wake_model.predict(audio)
        now       = time.time()
        score     = prediction.get(_cfg("wake_word"), 0)

        # Accumulate or reset consecutive hit counter
        if score > _cfg("wake_threshold"):
            _hit_count += 1
        else:
            _hit_count = 0

        # Post-speech silence window check:
        # How long has it been since Numa last finished speaking?
        time_since_speech = now - _tts.speech_just_ended()
        in_post_speech_window = time_since_speech < POST_SPEECH_SILENCE_SEC

        # Fire only when ALL conditions are met:
        #   1. Enough consecutive confident hits
        #   2. Cooldown elapsed since last trigger
        #   3. Not already processing a previous command
        #   4. Not in the post-speech silence window (prevents self-trigger)
        if (
            _hit_count >= _cfg("wake_required_hits")
            and (now - _last_trigger_time) > _cfg("wake_cooldown_sec")
            and not state.is_processing()
            and not in_post_speech_window
        ):
            _last_trigger_time = now
            _hit_count         = 0

            # Stop Numa mid-speech if still talking
            _tts.interrupt()

            state.set_processing(True)
            print("\n[Numa] Wake word detected!")

            t = threading.Thread(
                target = on_wake_callback,
                name   = "WakeHandler",
                daemon = True,
            )
            t.start()

    print("[Numa] Listening for wake word...")

    try:
        with sd.RawInputStream(
            samplerate = SAMPLE_RATE,
            blocksize  = BLOCK_SIZE,
            dtype      = "int16",
            channels   = 1,
            callback   = _audio_callback,
        ):
            while state.is_running():
                time.sleep(0.1)

    except KeyboardInterrupt:
        pass

    except Exception as e:
        print(f"[Numa] Wake engine error: {e}")