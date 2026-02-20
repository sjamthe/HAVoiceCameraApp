import asyncio
from wyoming.client import AsyncTcpClient
from wyoming.info import Describe, Info
from wyoming.audio import AudioStart, AudioChunk
from wyoming.wake import Detect, Detection

# --- CONFIGURATION ---
HA_IP = "192.168.86.27"          # IP address of your Home Assistant server
HA_PORT = 10400               # Default openWakeWord port in HA
RTSP_URL = "rtsp://homeassistant.local:8555/nexus_cam_audio"
CHUNK_SIZE = 1280 * 2

async def send_audio(process, client, first_chunk):
    """Streams the audio, starting with our pre-buffered chunk."""
    try:
        await client.write_event(
            AudioChunk(rate=16000, width=2, channels=1, audio=first_chunk).event()
        )
        while True:
            audio_bytes = await process.stdout.readexactly(CHUNK_SIZE)
            await client.write_event(
                AudioChunk(rate=16000, width=2, channels=1, audio=audio_bytes).event()
            )
    except asyncio.IncompleteReadError:
        print("\n[!] FFmpeg stopped sending audio.")

async def receive_events(client):
    """Listens for the wake word trigger."""
    while True:
        event = await client.read_event()
        if event is None:
            print("\n[!] The Wyoming Server closed the connection.")
            break
        
        if Detection.is_type(event.type):
            detection = Detection.from_event(event)
            print(f"\n*** WAKE WORD DETECTED: '{detection.name}'! ***\n")

async def main():
    print("Starting camera stream...")
    ffmpeg_cmd = [
        'ffmpeg', '-i', RTSP_URL, '-f', 's16le', '-ar', '16000', 
        '-ac', '1', '-loglevel', 'quiet', '-'
    ]
    process = await asyncio.create_subprocess_exec(
        *ffmpeg_cmd, stdout=asyncio.subprocess.PIPE
    )
    
    print("Buffering first audio chunk to prevent server timeout...")
    try:
        first_chunk = await process.stdout.readexactly(CHUNK_SIZE)
    except asyncio.IncompleteReadError:
        print("[!] FFmpeg failed to connect to go2rtc stream.")
        return

    print(f"\nConnecting to {HA_IP}:{HA_PORT}...")
    try:
        async with AsyncTcpClient(HA_IP, HA_PORT) as client:
            
            # 1. SEND THE DESCRIBE EVENT FIRST
            print("Requesting server info...")
            await client.write_event(Describe().event())
            
            # 2. READ THE INFO RESPONSE
            info_event = await client.read_event()
            
            if info_event is None:
                print("[!] Server dropped connection before handshake.")
                return
                
            if Info.is_type(info_event.type):
                info = Info.from_event(info_event)
                available_models = [m.name for w in info.wake for m in w.models]
                print(f"Server Handshake OK. Loaded models: {available_models}")
                
                # If models are loaded, pick ok_nabu. Otherwise default to a fallback.
                if available_models:
                    target_model = "ok_nabu" if "ok_nabu" in available_models else available_models[0]
                else:
                    print("[!] Warning: Server reported no models! Forcing 'ok_nabu' anyway...")
                    target_model = "ok_nabu"
            else:
                print(f"[!] Received unexpected event type: {info_event.type}")
                return
            
            print(f"Requesting '{target_model}' detection...")
            await client.write_event(Detect(names=[target_model]).event())
            
            # Start streaming
            await client.write_event(AudioStart(rate=16000, width=2, channels=1).event())
            print("Streaming audio and listening...")
            
            done, pending = await asyncio.wait(
                [
                    asyncio.create_task(send_audio(process, client, first_chunk)),
                    asyncio.create_task(receive_events(client))
                ],
                return_when=asyncio.FIRST_COMPLETED
            )
            for p in pending:
                p.cancel()
                
    except ConnectionResetError:
        print("\n[!] Connection reset by peer.")
    except Exception as e:
        print(f"\n[!] Unexpected error: {e}")
    finally:
        if process.returncode is None:
            process.terminate()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nStopping...")