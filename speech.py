import sounddevice as sd
import whisper
import numpy as np
import winsound
import time

SAMPLE_RATE = 16000

# Use faster English-only model
whisper_model = whisper.load_model("tiny.en")


# ---------- AUTO CALIBRATION ----------
def calibrate_mic():
    print("🔧 Calibrating microphone...")
    print("Stay silent for 2 seconds...")

    volumes = []

    for _ in range(20):
        audio = sd.rec(800, samplerate=SAMPLE_RATE, channels=1, dtype="float32")
        sd.wait()
        volumes.append(np.mean(np.abs(audio)))

    baseline = np.mean(volumes)

    silence_threshold = baseline * 3.5   # slightly stricter
    mic_off_threshold = baseline * 0.05  # detect mic off

    print("Baseline noise:", baseline)
    print("Silence threshold:", silence_threshold)

    return silence_threshold, mic_off_threshold


SILENCE_THRESHOLD, MIC_OFF_THRESHOLD = calibrate_mic()


# ---------- LISTEN + TRANSCRIBE ----------
def listen_and_transcribe():
    print("🎤 Listening for command...")
    winsound.Beep(800, 120)

    audio_buffer = []
    silence_start = None

    MAX_SILENCE = 0.6
    MAX_RECORD_TIME = 5
    start_time = time.time()

    def callback(indata, frames, time_info, status):
        nonlocal silence_start

        audio = indata.copy()
        audio_buffer.append(audio)

        volume = np.mean(np.abs(audio))

        # Silence detection
        if volume < SILENCE_THRESHOLD:
            if silence_start is None:
                silence_start = time.time()
        else:
            silence_start = None

        # Stop conditions
        if silence_start and (time.time() - silence_start > MAX_SILENCE):
            raise sd.CallbackStop()

        if time.time() - start_time > MAX_RECORD_TIME:
            raise sd.CallbackStop()

    try:
        with sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="float32",
            callback=callback
        ):
            # Wait until stop is triggered
            while time.time() - start_time < MAX_RECORD_TIME:
                sd.sleep(50)

    except sd.CallbackStop:
        pass
    except Exception as e:
        print("Recording error:", e)

    if not audio_buffer:
        return ""

    recording = np.concatenate(audio_buffer, axis=0).flatten()

    print("🧠 Transcribing...")
    result = whisper_model.transcribe(recording, language="en")

    text = result["text"].strip().lower()

    print("You said:", text)
    winsound.Beep(1200, 120)

    return text
