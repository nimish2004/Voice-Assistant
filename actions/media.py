"""
actions/media.py — Media playback control.

Uses global media keys via pyautogui so it works with any
currently active media player (Spotify, YouTube, VLC, etc.)
without coupling to a specific app.
"""

import pyautogui
from tts import speak


def play_music(data: dict):
    speak("Playing.")
    pyautogui.press("playpause")


def pause_music(data: dict):
    speak("Paused.")
    pyautogui.press("playpause")


def next_track(data: dict):
    speak("Next track.")
    pyautogui.press("nexttrack")


def prev_track(data: dict):
    speak("Previous track.")
    pyautogui.press("prevtrack")
