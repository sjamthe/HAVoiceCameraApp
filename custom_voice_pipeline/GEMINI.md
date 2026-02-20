# GEMINI.md - Custom Voice Pipeline for Home Assistant

This project is a experimental voice pipeline designed to bridge Home Assistant's voice capabilities with external audio sources (like IP cameras) using `openwakeword` and the `Wyoming` protocol.

## Project Overview

The **Custom Voice Pipeline** allows for real-time wake word detection from RTSP audio streams. It serves as a testing ground for different audio processing architectures:
1.  **Local Detection (`listen_raw.py`)**: Uses the `openwakeword` library to process audio locally via a `numpy` buffer.
2.  **Wyoming Integration (`listen_wyoming.py`)**: Streams audio to a Home Assistant Wyoming server (e.g., the `openwakeword` add-on) for detection.

### Main Technologies
- **Python**: Core logic using `asyncio` for non-blocking I/O.
- **Wyoming Protocol**: Standard protocol for Home Assistant voice satellite communication.
- **openwakeword**: A fast, local wake word detection library.
- **FFmpeg**: Used to ingest and transcode RTSP audio streams into raw PCM.
- **uv**: Modern Python package manager.

## Building and Running

### Prerequisites
- [uv](https://github.com/astral-sh/uv) installed on your system.
- `ffmpeg` installed and available in your PATH.
- A running `go2rtc` or RTSP stream providing audio (e.g., `rtsp://homeassistant.local:8555/nexus_cam_audio`).

### Installation
Sync dependencies and set up the virtual environment:
```bash
uv sync
```

### Running the Pipeline

**For local detection (Hey Jarvis):**
```bash
uv run listen_raw.py
```

**For Wyoming-based detection (Home Assistant integration):**
```bash
uv run listen_wyoming.py
```
*Note: Ensure `HA_IP` and `HA_PORT` in `listen_wyoming.py` match your Home Assistant's Wyoming server configuration.*

## Development Conventions

- **Audio Format**: All scripts normalize audio to **Raw PCM 16-bit Mono at 16,000Hz** via FFmpeg.
- **Asynchronous Execution**: The Wyoming client and stream ingestion use `asyncio` to handle concurrent event reading and audio writing.
- **Dependency Management**: Add new dependencies using `uv add <package>`.
- **Configuration**: Connection parameters (IPs, Ports, RTSP URLs) are currently hardcoded in the script headers for ease of development.
