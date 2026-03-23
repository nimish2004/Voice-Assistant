import os
import pyautogui
import datetime
import subprocess
import webbrowser
import urllib.parse
import requests as req
import psutil
from tts import speak
from pycaw.pycaw import AudioUtilities
from memory import clear_memory

# ---------- HELPERS ----------

def set_system_volume(percent):
    percent = max(0, min(100, percent))
    devices = AudioUtilities.GetSpeakers()
    volume = devices.EndpointVolume
    volume.SetMasterVolumeLevelScalar(percent / 100.0, None)
    speak(f"Setting volume to {percent} percent")

# ---------- MEDIA ACTIONS ----------

def play_music(data):
    speak("Playing music.")
    pyautogui.press("playpause")

def pause_music(data):
    speak("Pausing music.")
    pyautogui.press("playpause")

def next_track(data):
    speak("Playing next track.")
    pyautogui.press("nexttrack")

def prev_track(data):
    speak("Playing previous track.")
    pyautogui.press("prevtrack")

# ---------- APP ACTIONS ----------

def open_chrome(data):
    speak("Opening Google Chrome.")
    os.system("start chrome")

def open_spotify(data):
    speak("Opening Spotify.")
    os.system("start spotify")

def open_vscode(data):
    speak("Opening VS Code.")
    os.system("code")

def open_notepad(data):
    speak("Opening Notepad.")
    os.system("notepad")

def open_youtube(data):
    speak("Opening YouTube.")
    os.system("start https://www.youtube.com")

# ---------- WEB SEARCH ----------

def web_search(data):
    query = data.get("parameters", {}).get("query", "") or data.get("query", "")
    if not query:
        speak("What would you like me to search for?")
        return
    speak(f"Searching for {query}.")
    url = "https://www.google.com/search?q=" + urllib.parse.quote(query)
    webbrowser.open(url)

# ---------- WEATHER ----------

def get_weather(data):
    city = data.get("parameters", {}).get("city", "") or data.get("city", "")
    city = city.strip() if city else "auto"
    try:
        speak("Let me check the weather.")
        url = f"https://wttr.in/{urllib.parse.quote(city)}?format=3"
        response = req.get(url, timeout=5)
        if response.status_code == 200:
            weather_text = response.text.strip()
            speak(weather_text)
            print("Weather:", weather_text)
        else:
            speak("I couldn't fetch the weather right now.")
    except Exception as e:
        print("Weather error:", e)
        speak("I couldn't reach the weather service.")

# ---------- OPEN ANY APP ----------

def open_app(data):
    app_name = data.get("parameters", {}).get("app", "") or data.get("app", "")
    if not app_name:
        speak("Which app would you like me to open?")
        return
    speak(f"Opening {app_name}.")
    try:
        os.system(f"start {app_name}")
    except Exception as e:
        print("App open error:", e)
        speak(f"I couldn't open {app_name}.")

# ---------- SYSTEM ACTIONS ----------

def lock_laptop(data):
    speak("Locking laptop.")
    os.system("rundll32.exe user32.dll,LockWorkStation")

def shutdown(data):
    speak("Shutting down the system.")
    os.system("shutdown /s /t 5")

def restart(data):
    speak("Restarting the system.")
    os.system("shutdown /r /t 5")

def sleep(data):
    speak("Putting the system to sleep.")
    os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")

def mute(data):
    speak("Muting volume.")
    pyautogui.press("volumemute")

def volume_up(data):
    speak("Increasing volume.")
    pyautogui.press("volumeup")

def volume_down(data):
    speak("Decreasing volume.")
    pyautogui.press("volumedown")

def set_volume(data):
    value = data.get("value") or data.get("parameters", {}).get("value", 50)
    try:
        percent = int(value)
    except:
        percent = 50
    set_system_volume(percent)

def take_screenshot(data):
    speak("Taking a screenshot.")
    img = pyautogui.screenshot()
    folder = "screenshots"
    os.makedirs(folder, exist_ok=True)
    filename = os.path.join(folder, f"screenshot_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
    img.save(filename)
    speak(f"Screenshot saved.")
    print(f"Screenshot saved to: {filename}")

# ---------- INFO ----------

def tell_time(data):
    now = datetime.datetime.now().strftime("%H:%M")
    speak(f"The time is {now}")

def tell_date(data):
    today = datetime.datetime.now().strftime("%d %B %Y")
    speak(f"Today is {today}")

def battery_status(data):
    battery = psutil.sensors_battery()
    if battery:
        speak(f"Battery is at {battery.percent} percent.")
    else:
        speak("Battery info not available.")

# ---------- DEV ----------

def open_terminal(data):
    speak("Opening terminal.")
    os.system("start cmd")

def git_status(data):
    try:
        output = subprocess.check_output("git status", shell=True, text=True)
        print(output)
    except:
        print("Not a git repository")

# ---------- MEMORY ----------

def forget_everything(data):
    clear_memory()
    speak("Done, I've cleared my memory.")

# ---------- EXIT ----------

def exit_app(data):
    speak("Goodbye.")
    import state
    state.RUNNING = False

# ======================================================
# 🔥 INTENT MAP (THIS IS THE IMPORTANT PART)
# ======================================================

INTENT_MAP = {
    # Media
    "play_music": play_music,
    "pause_music": pause_music,
    "next_track": next_track,
    "prev_track": prev_track,

    # Apps
    "open_chrome": open_chrome,
    "open_spotify": open_spotify,
    "open_vscode": open_vscode,
    "open_notepad": open_notepad,
    "open_youtube": open_youtube,
    "open_app": open_app,

    # Web
    "web_search": web_search,
    "get_weather": get_weather,

    # System
    "lock_laptop": lock_laptop,
    "shutdown": shutdown,
    "restart": restart,
    "sleep": sleep,
    "mute": mute,
    "volume_up": volume_up,
    "volume_down": volume_down,
    "set_volume": set_volume,
    "take_screenshot": take_screenshot,

    # Info
    "tell_time": tell_time,
    "tell_date": tell_date,
    "battery_status": battery_status,

    # Dev
    "open_terminal": open_terminal,
    "git_status": git_status,

    # Memory
    "clear_memory": forget_everything,

    # Exit
    "exit": exit_app
}

# ---------- MAIN HANDLER ----------

def handle_intent(data):
    intent = data.get("intent")
    action = INTENT_MAP.get(intent)

    if action:
        action(data)
    else:
        print("I don't know how to do that yet.")
        speak("I don't know how to do that yet.")