"""
speech.py — Microphone input and speech-to-text for Numa.

Key design decisions:
  - Calibration is non-blocking and skippable; result is cached to disk
    so startup is instant on subsequent launches.
  - Recording uses a threading.Event to signal stop cleanly from the
    audio callback — no race condition on silence_start.
  - Minimum audio gate (MIN_AUDIO_SECONDS) prevents Whisper from
    hallucinating text on mic glitches or near-silence recordings.
  - Whisper runs on the calling thread (already a daemon thread from
    wakeword.py) so it never blocks the main loop or wake engine.
  - Beep sounds loaded from assets/ — falls back to winsound if missing.
"""

import json
import os
import threading
import time

import numpy as np
import sounddevice as sd
import whisper

# ── Config ────────────────────────────────────────────────────────────────────

SAMPLE_RATE      = 16000
MAX_SILENCE_SEC  = 0.8    # seconds of silence before cutting off recording
MAX_RECORD_SEC   = 10     # hard ceiling on recording length
MIN_AUDIO_SEC    = 0.4    # minimum speech length — below this we discard
CALIBRATION_FILE = "calibration.json"
NOISE_MULTIPLIER = 3.5    # silence threshold = baseline * this value

# ── Whisper model ─────────────────────────────────────────────────────────────

print("🔄  Loading Whisper model...")
_whisper_model = whisper.load_model("base.en")
print("✅  Whisper ready.")

# ── Calibration ───────────────────────────────────────────────────────────────

def _run_calibration() -> tuple[float, float]:
    """
    Sample ambient noise for ~1 second and compute thresholds.
    Returns (silence_threshold, mic_off_threshold).
    """
    print("🔧  Calibrating microphone — stay silent...")
    samples = []

    for _ in range(15):
        chunk = sd.rec(800, samplerate=SAMPLE_RATE, channels=1, dtype="float32")
        sd.wait()
        samples.append(float(np.mean(np.abs(chunk))))

    baseline          = float(np.mean(samples))
    silence_threshold = baseline * NOISE_MULTIPLIER
    mic_off_threshold = baseline * 0.05

    result = {
        "baseline"          : baseline,
        "silence_threshold" : silence_threshold,
        "mic_off_threshold" : mic_off_threshold,
    }

    # Cache to disk — next startup skips calibration entirely
    try:
        with open(CALIBRATION_FILE, "w") as f:
            json.dump(result, f, indent=2)
    except Exception as e:
        print(f"⚠️  Could not cache calibration: {e}")

    print(f"   Baseline: {baseline:.6f}  |  Threshold: {silence_threshold:.6f}")
    return silence_threshold, mic_off_threshold


def _load_calibration() -> tuple[float, float] | None:
    """Load cached calibration from disk. Returns None if missing/stale."""
    if not os.path.exists(CALIBRATION_FILE):
        return None
    try:
        with open(CALIBRATION_FILE) as f:
            data = json.load(f)
        st = data["silence_threshold"]
        mo = data["mic_off_threshold"]
        print(f"✅  Calibration loaded from cache (threshold: {st:.6f})")
        return st, mo
    except Exception:
        return None


def calibrate(force: bool = False) -> tuple[float, float]:
    """
    Public calibration entry point.
    Uses cached values unless force=True or cache is missing.
    """
    if not force:
        cached = _load_calibration()
        if cached:
            return cached
    return _run_calibration()


# Load at module import — fast on second run (cache hit)
SILENCE_THRESHOLD, MIC_OFF_THRESHOLD = calibrate()


# ── Audio feedback ─────────────────────────────────────────────────────────────

def _beep(freq: int, duration_ms: int):
    """Play a beep. Silent fail if winsound unavailable."""
    try:
        import winsound
        winsound.Beep(freq, duration_ms)
    except Exception:
        pass


# ── Core recording ─────────────────────────────────────────────────────────────

def _record_audio() -> np.ndarray | None:
    """
    Stream mic audio until:
      a) Silence detected for MAX_SILENCE_SEC, or
      b) MAX_RECORD_SEC elapsed.

    Uses threading.Event for clean cross-thread signaling — no race
    conditions on shared mutable state in the audio callback.

    Returns a flat float32 numpy array, or None if nothing was captured.
    """
    audio_buffer  : list[np.ndarray] = []
    stop_event    = threading.Event()
    silence_since : list[float | None] = [None]   # list so callback can mutate

    def _callback(indata, frames, time_info, status):
        chunk  = indata.copy()
        volume = float(np.mean(np.abs(chunk)))

        # Always buffer — we decide validity after recording stops
        audio_buffer.append(chunk)

        # ── Silence detection ─────────────────────────────────────────────
        if volume < SILENCE_THRESHOLD:
            if silence_since[0] is None:
                silence_since[0] = time.monotonic()
            elif time.monotonic() - silence_since[0] >= MAX_SILENCE_SEC:
                stop_event.set()
        else:
            silence_since[0] = None  # reset on any audible sound

    stream = sd.InputStream(
        samplerate = SAMPLE_RATE,
        channels   = 1,
        dtype      = "float32",
        callback   = _callback,
    )

    with stream:
        # Block until stop_event fires OR hard timeout expires
        stop_event.wait(timeout=MAX_RECORD_SEC)

    if not audio_buffer:
        return None

    return np.concatenate(audio_buffer, axis=0).flatten()


# ── Public interface ───────────────────────────────────────────────────────────

def listen_and_transcribe() -> str:
    """
    Record one voice command from the microphone and return the
    transcribed text (lowercase, stripped).

    Returns "" if:
      - No audio was captured
      - Audio was too short (mic glitch / noise burst)
      - Whisper returned an empty string
    """
    print("\n🎤  Listening...")
    _beep(800, 100)   # ready tone

    recording = _record_audio()

    if recording is None:
        print("⚠️  No audio captured.")
        return ""

    duration = len(recording) / SAMPLE_RATE
    if duration < MIN_AUDIO_SEC:
        print(f"⚠️  Audio too short ({duration:.2f}s) — discarding.")
        return ""

    print(f"🧠  Transcribing ({duration:.1f}s of audio)...")

    try:
        result = _whisper_model.transcribe(
            recording,
            language        = "en",
            condition_on_previous_text = False,   # faster, less hallucination
            fp16            = False,               # stable on CPU
        )
        text = result["text"].strip().lower()
    except Exception as e:
        print(f"❌  Whisper error: {e}")
        return ""

    _beep(1200, 100)  # done tone
    print(f"🗣️  Heard: \"{text}\"")
    return text


def recalibrate():
    """
    Force a fresh microphone calibration and update module-level thresholds.
    Called via voice command: 'recalibrate microphone'.
    """
    global SILENCE_THRESHOLD, MIC_OFF_THRESHOLD
    SILENCE_THRESHOLD, MIC_OFF_THRESHOLD = calibrate(force=True)
    print("✅  Recalibration complete.")