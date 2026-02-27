import os
import pyautogui
import datetime
import sys
import subprocess
import psutil
from state import RUNNING
from tts import speak
from ctypes import cast, POINTER
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from ctypes import cast, POINTER

# ---------- ACTION ENGINE v2 ----------

def set_system_volume(percent):
    percent = max(0, min(100, percent))

    devices = AudioUtilities.GetSpeakers()
    volume = devices.EndpointVolume

    volume.SetMasterVolumeLevelScalar(percent / 100.0, None)

    print(f"Volume set to {percent}%")

def handle_intent(data):
    intent = data.get("intent")

    # ===== MEDIA =====
    if intent == "play_music":
        print("Action: Play / Resume music")
        speak("Playing music.")
        pyautogui.press("playpause")

    elif intent == "pause_music":
        print("Action: Pause music")
        speak("Pausing music.")
        pyautogui.press("playpause")

    elif intent == "next_track":
        print("Action: Next track")
        speak("Playing next track.")
        pyautogui.press("nexttrack")

    elif intent == "prev_track":
        print("Action: Previous track")
        speak("Playing previous track.")
        pyautogui.press("prevtrack")

    # ===== APPS =====
    elif intent == "open_chrome":
        print("Action: Opening Chrome")
        speak("Opening Google Chrome.")
        os.system("start chrome")

    elif intent == "open_spotify":
        print("Action: Opening Spotify")
        speak("Opening Spotify.")
        os.system("start spotify")

    elif intent == "open_vscode":
        print("Action: Opening VS Code")
        speak("Opening VS Code.")
        os.system("code")

    elif intent == "open_notepad":
        print("Action: Opening Notepad")
        speak("Opening Notepad.")
        os.system("notepad")

    elif intent == "open_youtube":
        print("Action: Opening YouTube")
        speak("Opening YouTube.")
        os.system("start https://www.youtube.com")

    # ===== SYSTEM =====
    elif intent == "lock_laptop":
        print("Action: Locking laptop")
        speak("Locking laptop.")
        os.system("rundll32.exe user32.dll,LockWorkStation")

    elif intent == "shutdown":
        print("Action: Shutting down")
        speak("Shutting down the system.")
        os.system("shutdown /s /t 5")

    elif intent == "restart":
        print("Action: Restarting")
        speak("Restarting the system.")
        os.system("shutdown /r /t 5")

    elif intent == "sleep":
        print("Action: Sleeping")
        speak("Putting the system to sleep.")
        os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")

    elif intent == "mute":
        print("Action: Muting volume")
        speak("Muting volume.")
        pyautogui.press("volumemute")

    elif intent == "volume_up":
        print("Action: Volume up")
        speak("Increasing volume.")
        pyautogui.press("volumeup")

    elif intent == "volume_down":
        print("Action: Volume down")
        speak("Decreasing volume.")
        pyautogui.press("volumedown")

    elif intent == "set_volume":
        # Try direct value
        value = data.get("value")

        # If model sends nested parameters
        if not value and "parameters" in data:
            value = data["parameters"].get("value")

        try:
            percent = int(value)
        except:
            percent = 50

        percent = max(0, min(100, percent))

        print(f"Action: Setting volume to {percent}%")
        set_system_volume(percent)
        speak(f"Setting volume to {percent} percent")

    elif intent == "take_screenshot":
        print("Action: Taking screenshot")
        speak("Taking a screenshot.")
        img = pyautogui.screenshot()
        filename = f"screenshot_{datetime.datetime.now().strftime('%H%M%S')}.png"
        img.save(filename)
        print("Saved:", filename)

    # ===== INFO =====
    elif intent == "tell_time":
        now = datetime.datetime.now().strftime("%H:%M")
        print("Time:", now)
        speak(f"The time is {now}.")

    elif intent == "tell_date":
        today = datetime.datetime.now().strftime("%d %B %Y")
        print("Date:", today)
        speak(f"Today is {today}.")

    elif intent == "battery_status":
        battery = psutil.sensors_battery()
        if battery:
            print(f"Battery: {battery.percent}%")
            speak(f"Battery is at {battery.percent} percent.")
        else:
            speak("Battery information is not available.")

    # ===== DEV MODE =====
    elif intent == "open_terminal":
        print("Action: Opening terminal")
        speak("Opening terminal.")
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
        speak("Goodbye.")
        import state
        state.RUNNING = False

    # ===== FALLBACK =====
    else:
        print("I don't know how to do that yet.")