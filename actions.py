import os
import pyautogui
import datetime
import sys
import subprocess
import psutil

# ---------- ACTION ENGINE v2 ----------

def handle_intent(intent):
    
    # ===== MEDIA =====
    if intent == "play_music":
        print("Action: Play / Resume music")
        pyautogui.press("playpause")

    elif intent == "pause_music":
        print("Action: Pause music")
        pyautogui.press("playpause")

    elif intent == "next_track":
        print("Action: Next track")
        pyautogui.press("nexttrack")

    elif intent == "prev_track":
        print("Action: Previous track")
        pyautogui.press("prevtrack")

    # ===== APPS =====
    elif intent == "open_chrome":
        print("Action: Opening Chrome")
        os.system("start chrome")

    elif intent == "open_spotify":
        print("Action: Opening Spotify")
        os.system("start spotify")

    elif intent == "open_vscode":
        print("Action: Opening VS Code")
        os.system("code")

    elif intent == "open_notepad":
        print("Action: Opening Notepad")
        os.system("notepad")

    elif intent == "open_youtube":
        print("Action: Opening YouTube")
        os.system("start https://www.youtube.com")

    # ===== SYSTEM =====
    elif intent == "lock_laptop":
        print("Action: Locking laptop")
        os.system("rundll32.exe user32.dll,LockWorkStation")

    elif intent == "shutdown":
        print("Action: Shutting down")
        os.system("shutdown /s /t 5")

    elif intent == "restart":
        print("Action: Restarting")
        os.system("shutdown /r /t 5")

    elif intent == "sleep":
        print("Action: Sleeping")
        os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")

    elif intent == "mute":
        print("Action: Muting volume")
        pyautogui.press("volumemute")

    elif intent == "volume_up":
        print("Action: Volume up")
        pyautogui.press("volumeup")

    elif intent == "volume_down":
        print("Action: Volume down")
        pyautogui.press("volumedown")

    elif intent == "take_screenshot":
        print("Action: Taking screenshot")
        img = pyautogui.screenshot()
        filename = f"screenshot_{datetime.datetime.now().strftime('%H%M%S')}.png"
        img.save(filename)
        print("Saved:", filename)

    # ===== INFO =====
    elif intent == "tell_time":
        now = datetime.datetime.now().strftime("%H:%M")
        print("Time:", now)

    elif intent == "tell_date":
        today = datetime.datetime.now().strftime("%d %B %Y")
        print("Date:", today)

    elif intent == "battery_status":
        battery = psutil.sensors_battery()
        if battery:
            print(f"Battery: {battery.percent}%")
        else:
            print("Battery info not available")

    # ===== DEV MODE =====
    elif intent == "open_terminal":
        print("Action: Opening terminal")
        os.system("start cmd")

    elif intent == "git_status":
        print("Action: Git status")
        try:
            output = subprocess.check_output("git status", shell=True, text=True)
            print(output)
        except:
            print("Not a git repository")

    # ===== EXIT =====
    elif intent == "exit":
        print("Goodbye 👋")
        sys.exit(0)

    # ===== FALLBACK =====
    else:
        print("I don't know how to do that yet.")
