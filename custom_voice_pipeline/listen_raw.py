import subprocess
import numpy as np
import openwakeword
from openwakeword.model import Model

# 1. Initialize the Wake Word Model
# openwakeword downloads the default models automatically, 
# or you can point it to a custom .tflite / .onnx file if you trained "okay_nabu" yourself.
print("Loading Wake Word model...")
oww_model = Model()

# 2. Connect to go2rtc
# Replace with your actual go2rtc RTSP or API stream URL
GO2RTC_STREAM_URL = "rtsp://homeassistant.local:8555/nexus_cam_audio"

ffmpeg_cmd = [
    'ffmpeg',
    '-i', GO2RTC_STREAM_URL,
    '-f', 's16le',       # Raw PCM 16-bit (required by openwakeword)
    '-ar', '16000',      # 16 kHz sample rate
    '-ac', '1',          # Mono channel
    '-loglevel', 'quiet',
    '-'                  # Stream output directly to Python stdout
]

print(f"Connecting to stream at {GO2RTC_STREAM_URL}...")
process = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE, bufsize=10**8)

# openwakeword works best with 80ms chunks (1280 samples at 16kHz)
CHUNK_SIZE = 1280 

print("Listening for 'Hey Jarvis'...")

try:
    while True:
        # Read 2 bytes per sample
        raw_audio = process.stdout.read(CHUNK_SIZE * 2)
        if not raw_audio:
            print("Stream ended or disconnected.")
            break
            
        # Convert raw bytes to numpy array
        audio_data = np.frombuffer(raw_audio, dtype=np.int16)
        
        # 3. Feed audio chunk to the model
        prediction = oww_model.predict(audio_data)
        
        # 4. Check the confidence score (0.0 to 1.0)
        # You can print(prediction) here to observe the score jumping in real-time
        if prediction.get('hey_jarvis', 0) > 0.5:
            print("\n*** WAKE WORD DETECTED: 'Hey Jarvis'! ***\n")
            
            # ---------------------------------------------------------
            # NEXT STEP: GOOGLE STT LOGIC GOES HERE
            # 1. Read the next ~5 seconds of process.stdout.read()
            # 2. Send that exact buffer to the Google Cloud Speech API
            # ---------------------------------------------------------
            
            # For testing, we will just reset and keep listening, 
            # or you can `break` to stop the script.
            oww_model.reset()

except KeyboardInterrupt:
    print("\nStopping...")
finally:
    process.terminate()
