import sounddevice as sd
import whisper
import numpy as np
import scipy.io.wavfile as wav
import winsound
import time

SAMPLE_RATE = 16000
TEMP_AUDIO_FILE = "command.wav"

whisper_model = whisper.load_model("small")

# ---------- AUTO CALIBRATION ----------
def calibrate_mic():
    print("🔧 Calibrating microphone...")
    print("Stay silent for 2 seconds...")

    volumes = []

    for _ in range(20):
        audio = sd.rec(800, samplerate=SAMPLE_RATE, channels=1)
        sd.wait()
        volumes.append(np.mean(np.abs(audio)))

    baseline = np.mean(volumes)
    silence_threshold = baseline * 3
    mic_off_threshold = baseline * 0.1

    print("Baseline noise:", baseline)
    print("Silence threshold:", silence_threshold)
    print("Mic-off threshold:", mic_off_threshold)

    return silence_threshold, mic_off_threshold

SILENCE_THRESHOLD, MIC_OFF_THRESHOLD = calibrate_mic()


# ---------- LISTEN + TRANSCRIBE ----------
def listen_and_transcribe():
    print("🎤 Listening for command...")
    winsound.Beep(800, 150)

    audio_buffer = []
    silence_start = None

    MAX_SILENCE = 0.7
    MAX_RECORD_TIME = 4
    start_time = time.time()

    def callback(indata, frames, time_info, status):
        nonlocal silence_start
        audio = indata.copy()
        audio_buffer.append(audio)

        volume = np.mean(np.abs(audio))

        # Detect mic muted
        if volume < MIC_OFF_THRESHOLD:
            print("⚠️ Microphone seems muted")

        # Silence logic
        if volume < SILENCE_THRESHOLD:
            if silence_start is None:
                silence_start = time.time()
        else:
            silence_start = None

        # Stop on silence
        if silence_start and time.time() - silence_start > MAX_SILENCE:
            raise sd.CallbackStop()

        # Safety stop
        if time.time() - start_time > MAX_RECORD_TIME:
            raise sd.CallbackStop()

    try:
        with sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            callback=callback
        ):
            sd.sleep(20000)
    except:
        pass

    recording = np.concatenate(audio_buffer, axis=0)
    wav.write(TEMP_AUDIO_FILE, SAMPLE_RATE, recording)

    print("🧠 Transcribing...")
    result = whisper_model.transcribe(TEMP_AUDIO_FILE)
    text = result["text"].strip().lower()

    print("You said:", text)
    winsound.Beep(1200, 150)
    return text
