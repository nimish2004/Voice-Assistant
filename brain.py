# ---------- BRAIN (INTENT ENGINE v2) ----------

def get_intent(text):
    text = text.lower().strip()

    # ===== MEDIA =====
    if "play" in text and "music" in text:
        return "play_music"

    elif "pause" in text or "stop music" in text:
        return "pause_music"

    elif "next" in text:
        return "next_track"

    elif "previous" in text or "back" in text:
        return "prev_track"

    # ===== APPS =====
    elif "open" in text and "chrome" in text:
        return "open_chrome"

    elif "open" in text and "spotify" in text:
        return "open_spotify"

    elif "open" in text and "vscode" in text:
        return "open_vscode"

    elif "open" in text and "notepad" in text:
        return "open_notepad"

    elif "open" in text and "youtube" in text:
        return "open_youtube"

    # ===== SYSTEM =====
    elif "lock" in text:
        return "lock_laptop"

    elif "shutdown" in text:
        return "shutdown"

    elif "restart" in text:
        return "restart"

    elif "sleep" in text:
        return "sleep"

    elif "mute" in text:
        return "mute"

    elif "volume up" in text or "increase volume" in text:
        return "volume_up"

    elif "volume down" in text or "decrease volume" in text:
        return "volume_down"

    elif "screenshot" in text:
        return "take_screenshot"

    # ===== INFO =====
    elif "time" in text:
        return "tell_time"

    elif "date" in text:
        return "tell_date"

    elif "battery" in text:
        return "battery_status"

    # ===== DEV MODE =====
    elif "open" in text and "terminal" in text:
        return "open_terminal"

    elif "git status" in text:
        return "git_status"

    # ===== EXIT =====
    elif "exit" in text or "quit" in text or "goodbye" in text:
        return "exit"

    # ===== FALLBACK =====
    else:
        return "unknown"
