"""
wakeword.py - Wake word detection engine for Numa.

Key behaviours:
  - POST_SPEECH_SILENCE_SEC: ignores detections for 2s after Numa speaks.
    Prevents Numa's TTS from self-triggering. Was 1.5s, increased to 2.0s
    based on real-world testing showing false triggers still occurring.

  - REQUIRED_HITS: requires 3 consecutive confident frames before firing.
    Reduces single-frame noise false positives.

  - Processing lock: never fires while a command is being processed.
    Prevents overlapping wake events.

  - tts.interrupt(): stops Numa mid-speech when user triggers wake word.
    User doesn't need to wait for Numa to finish talking.
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

# Seconds after Numa finishes speaking to ignore wake detections.
# 2.0s works better than 1.5s for faster speakers and louder speakers.
POST_SPEECH_SILENCE_SEC = 2.0


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
    Block the calling thread, streaming mic audio.
    Fires on_wake_callback in a daemon thread on confident wake detection.
    """
    global _last_trigger_time, _hit_count

    def _audio_callback(indata, frames, time_info, status):
        global _last_trigger_time, _hit_count

        audio      = np.frombuffer(indata, dtype=np.int16)
        prediction = _wake_model.predict(audio)
        now        = time.time()
        score      = prediction.get(_cfg("wake_word"), 0)

        # Accumulate or reset confidence counter
        if score > _cfg("wake_threshold"):
            _hit_count += 1
        else:
            _hit_count = 0

        # How long since Numa last finished speaking
        time_since_speech   = now - _tts.speech_just_ended()
        in_post_speech_win  = time_since_speech < POST_SPEECH_SILENCE_SEC

        # Fire when ALL conditions met:
        # 1. Enough consecutive confident frames
        # 2. Cooldown since last trigger elapsed
        # 3. Not already processing a command
        # 4. Not in post-speech silence window (prevents self-trigger)
        if (
            _hit_count          >= _cfg("wake_required_hits")
            and (now - _last_trigger_time) > _cfg("wake_cooldown_sec")
            and not state.is_processing()
            and not in_post_speech_win
        ):
            _last_trigger_time = now
            _hit_count         = 0

            _tts.interrupt()
            state.set_processing(True)
            print("\n[Numa] Wake word detected!")

            threading.Thread(
                target = on_wake_callback,
                name   = "WakeHandler",
                daemon = True,
            ).start()

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