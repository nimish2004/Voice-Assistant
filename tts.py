"""
tts.py — Text-to-speech output for Numa.

Architecture:
  Primary   : edge-tts (Microsoft neural voices, requires internet)
              Runs on a dedicated persistent asyncio event loop in a
              background thread — no "event loop closed" crashes.
  Fallback  : pyttsx3 (fully offline, Windows SAPI voices)
              Single engine instance created once and reused.

Key behaviours:
  - speak() is synchronous from the caller's perspective — it blocks
    until audio finishes, which is correct for a voice assistant
    (we don't want overlapping speech).
  - interrupt() stops playback immediately — called by wakeword.py
    when wake word fires mid-speech so Numa doesn't keep talking
    while the user is already giving the next command.
  - Mute state is read from state.py — 'mute Numa' voice command
    suppresses all TTS output without killing the engine.
  - Temp MP3 files are always cleaned up via try/finally, even on crash.
  - All public functions are thread-safe.
"""

import asyncio
import os
import tempfile
import threading

import pygame
import state

# ── Config ────────────────────────────────────────────────────────────────────

VOICE       = "en-US-BrianNeural"   # calm, natural male — works well at speed
VOICE_RATE  = "+5%"                  # slightly faster than default
VOICE_PITCH = "+0Hz"

# ── pygame mixer ──────────────────────────────────────────────────────────────

pygame.mixer.init()
_playback_lock = threading.Lock()    # only one audio stream at a time

# ── Persistent asyncio event loop (edge-tts) ──────────────────────────────────
#
# asyncio.run() creates + destroys an event loop every call.
# On Windows, this causes "Event loop is closed" errors on rapid calls.
# Fix: one persistent loop running in a dedicated daemon thread.

_loop   = asyncio.new_event_loop()
_thread = threading.Thread(
    target  = _loop.run_forever,
    name    = "TTS-AsyncLoop",
    daemon  = True,
)
_thread.start()

# ── pyttsx3 singleton (offline fallback) ──────────────────────────────────────
#
# pyttsx3 leaks COM objects if you call init() repeatedly on Windows.
# Create once, reuse forever.

_pyttsx3_engine = None
_pyttsx3_lock   = threading.Lock()

def _get_pyttsx3():
    global _pyttsx3_engine
    with _pyttsx3_lock:
        if _pyttsx3_engine is None:
            try:
                import pyttsx3
                _pyttsx3_engine = pyttsx3.init()
                _pyttsx3_engine.setProperty("rate", 175)
                _pyttsx3_engine.setProperty("volume", 1.0)
            except Exception as e:
                print(f"⚠️  pyttsx3 init failed: {e}")
        return _pyttsx3_engine


# ── edge-tts implementation ───────────────────────────────────────────────────

async def _synthesise(text: str, path: str):
    """Generate MP3 from edge-tts and save to path."""
    import edge_tts
    communicate = edge_tts.Communicate(text, VOICE, rate=VOICE_RATE, pitch=VOICE_PITCH)
    await communicate.save(path)


def _play_mp3(path: str):
    """Play an MP3 file via pygame, blocking until done or interrupted."""
    with _playback_lock:
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.wait(50)
            pygame.mixer.music.unload()
        except Exception as e:
            print(f"⚠️  pygame playback error: {e}")


def _speak_edge(text: str) -> bool:
    """
    Speak using edge-tts + pygame.
    Returns True on success, False on any failure.
    """
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            tmp_path = f.name

        # Submit coroutine to our persistent loop and wait for result
        future = asyncio.run_coroutine_threadsafe(_synthesise(text, tmp_path), _loop)
        future.result(timeout=10)   # 10s network timeout

        _play_mp3(tmp_path)
        return True

    except Exception as e:
        print(f"⚠️  edge-tts error: {e}")
        return False

    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass   # file in use — OS will clean it on reboot


def _speak_pyttsx3(text: str):
    """Speak using pyttsx3 (fully offline fallback)."""
    engine = _get_pyttsx3()
    if engine is None:
        print("❌  No TTS engine available.")
        return
    try:
        with _playback_lock:
            engine.say(text)
            engine.runAndWait()
    except Exception as e:
        print(f"❌  pyttsx3 error: {e}")


# ── Public interface ───────────────────────────────────────────────────────────

def speak(text: str):
    """
    Speak text aloud. Blocks until playback is complete.

    Respects mute state from state.py — silent when muted.
    Tries edge-tts first; falls back to pyttsx3 if it fails.
    """
    if not text or not text.strip():
        return

    print(f"🔊  Numa: {text}")

    if state.is_muted():
        print("   (muted — skipping audio)")
        return

    # Primary: edge-tts (neural voice, needs internet)
    success = _speak_edge(text)

    # Fallback: pyttsx3 (offline, robotic but always available)
    if not success:
        print("🔄  Falling back to offline TTS...")
        _speak_pyttsx3(text)


def interrupt():
    """
    Stop any currently playing audio immediately.
    Called by wakeword.py when wake word fires mid-speech.
    """
    try:
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()
            pygame.mixer.music.unload()
    except Exception:
        pass


def set_voice(short_name: str):
    """
    Change the edge-tts voice at runtime.
    Example: set_voice("en-GB-SoniaNeural")
    """
    global VOICE
    VOICE = short_name
    print(f"✅  Voice changed to: {short_name}")