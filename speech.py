import sounddevice as sd
import whisper
import scipy.io.wavfile as wav
import winsound

# ---------- CONFIG ----------
SAMPLE_RATE = 16000
RECORD_SECONDS = 4
TEMP_AUDIO_FILE = "command.wav"

# ---------- LOAD MODEL ----------
whisper_model = whisper.load_model("base")

print("Speech engine loaded (Whisper).")

# ---------- CORE FUNCTION ----------
def listen_and_transcribe():
    print("🎤 Listening for command...")
    winsound.Beep(800, 150)

    recording = sd.rec(
        int(RECORD_SECONDS * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="int16"
    )
    sd.wait()

    wav.write(TEMP_AUDIO_FILE, SAMPLE_RATE, recording)

    print("🧠 Transcribing...")
    result = whisper_model.transcribe(TEMP_AUDIO_FILE)
    text = result["text"].strip().lower()

    print("You said:", text)
    winsound.Beep(1200, 150)

    return text
