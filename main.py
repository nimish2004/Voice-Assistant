"""
main.py — Entry point for Numa Personal Voice Assistant.

Pipeline:
    wakeword.py  →  speech.py  →  llm_brain.py  →  actions/registry.py
         ↑                                               ↓
         └──────────────── main.py (orchestrator) ───────┘
"""

import sys
import state
from config.settings import settings
from wakeword import start_wake_engine
from speech import listen_and_transcribe
from llm_brain import get_intent_llm
from actions import handle_intent
from tts import speak


# ── Startup banner ────────────────────────────────────────────────────────────

def print_banner():
    wake_word = settings.get("wake_word").title()
    print()
    print("╔══════════════════════════════════════╗")
    print("║     Numa — Personal Voice Assistant   ║")
    print("╠══════════════════════════════════════╣")
    print(f"║  Wake word : {wake_word:<25} ║")
    print("║  Press Ctrl+C to stop                 ║")
    print("╚══════════════════════════════════════╝")
    print(f"  Settings : {settings.get_settings_file_path()}")
    print()


# ── Wake event handler ────────────────────────────────────────────────────────

def on_wake():
    """
    Called in a daemon thread each time the wake word is detected.
    The processing lock in wakeword.py guarantees this never runs
    concurrently with itself.
    """
    try:
        # ── Step 1: Listen ────────────────────────────────────────────────
        text = listen_and_transcribe()

        if not text or len(text.split()) < 2:
            print("⚠️  Too short — ignoring.")
            return

        print(f"\n🗣️  You said : {text}")

        # ── Step 2: Think (LLM → intent) ─────────────────────────────────
        result = get_intent_llm(text)
        print(f"🧠  Intent   : {result}")

        # ── Step 3: Act ───────────────────────────────────────────────────
        rtype = result.get("type")

        if rtype == "task":
            handle_intent(result)

        elif rtype == "chat":
            reply = result.get("response", "")
            if reply:
                speak(reply)

        else:
            print("⚠️  Unknown response type from LLM.")

    except Exception as e:
        # Never crash the wake engine — just log and keep listening
        print(f"❌  Error in on_wake: {e}")

    finally:
        # Always release the processing lock so the next wake can fire
        state.set_processing(False)


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    print_banner()
    speak(settings.get("startup_greeting"))

    try:
        start_wake_engine(on_wake)          # blocks until state.is_running() → False

    except KeyboardInterrupt:
        print("\n\n👋  Ctrl+C received — shutting down Numa.")

    finally:
        state.stop()                        # ensure flag is set even on crash
        print("✅  Numa stopped cleanly.")
        sys.exit(0)


if __name__ == "__main__":
    main()
