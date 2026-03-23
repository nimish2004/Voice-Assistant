import asyncio
import edge_tts
import tempfile
import os
import pygame

# Microsoft neural voice — sounds very natural
# To list voices: py -3.10 -c "import asyncio, edge_tts; voices = asyncio.run(edge_tts.list_voices()); [print(v['ShortName']) for v in voices if 'en-' in v['ShortName']]"
VOICE = "en-US-BrianNeural"  # calm, natural male voice

# Initialize pygame mixer once
pygame.mixer.init()


async def _speak_async(text):
    communicate = edge_tts.Communicate(text, VOICE, rate="+5%")

    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        tmp_path = f.name

    try:
        await communicate.save(tmp_path)

        # Play silently using pygame — no window opens
        pygame.mixer.music.load(tmp_path)
        pygame.mixer.music.play()

        # Wait until playback finishes
        while pygame.mixer.music.get_busy():
            pygame.time.wait(100)

        pygame.mixer.music.unload()
    finally:
        try:
            os.remove(tmp_path)
        except:
            pass


def speak(text):
    print("Assistant:", text)
    try:
        asyncio.run(_speak_async(text))
    except Exception as e:
        print(f"TTS Error: {e}")
        # Fallback to pyttsx3 if edge-tts fails
        try:
            import pyttsx3
            engine = pyttsx3.init()
            engine.setProperty('rate', 175)
            engine.say(text)
            engine.runAndWait()
        except:
            pass