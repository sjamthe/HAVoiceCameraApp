# GEMINI.md - Voice Camera Assistant for Home Assistant

This project is a Home Assistant Add-on that integrates Gemini AI with local camera snapshots to provide intelligent descriptions and answers about what the camera "sees."

## Project Overview

The **Voice Camera Assistant** acts as a bridge between Home Assistant's voice pipeline and Google's Gemini AI. When triggered, it:
1.  Captures a snapshot from an IP Webcam (typically an Android phone running IP Webcam app).
2.  Sends the image and a text prompt to the Gemini AI API.
3.  Posts the AI's response back to Home Assistant as a persistent notification.

### Main Technologies
- **Python**: Core application logic using `asyncio` and `aiohttp`.
- **Gemini AI API**: For multimodal image and text analysis.
- **Home Assistant Supervisor API**: For configuration and notifications.
- **Docker**: For containerized deployment as a Home Assistant Add-on.
- **Bashio**: For accessing Home Assistant configuration in the entry point script.

### Architecture
- **`voice_camera_assistant.py`**: The main service. It runs an internal HTTP server (port 8099) to receive triggers.
- **`config.yaml`**: Home Assistant Add-on manifest defining the UI options and permissions.
- **`run.sh`**: Entry point that translates Home Assistant configuration into a `config.json` for the Python script.
- **`Dockerfile`**: Defines the environment, installing Python dependencies like `aiohttp`.

## Building and Running

### Within Home Assistant
This project is designed to be installed as a **Local Add-on**.
1.  Copy the project folder to the `/addons` directory of your Home Assistant installation.
2.  Go to **Settings > Add-ons**, click **Add-on Store**, and select **Check for updates**.
3.  The "Voice Camera Assistant" should appear under "Local add-ons".
4.  Configure the `ipwebcam_host`, `ipwebcam_port`, and `gemini_api_key` in the add-on configuration tab.
5.  Start the add-on.

### Manual Trigger
The add-on listens for POST requests. You can trigger it manually via `curl`:
```bash
curl -X POST http://<addon-ip>:8099/trigger \
  -H 'Content-Type: application/json' \
  -d '{"prompt": "What do you see?"}'
```

### Development / Local Testing
To run the Python script locally (outside of Home Assistant):
1.  Create a `config.json` matching the structure expected by `voice_camera_assistant.py`.
2.  Install dependencies: `pip install aiohttp`.
3.  Run the script:
    ```bash
    python3 voice_camera_assistant.py --config config.json
    ```
    *Note: Notification logic depends on the `SUPERVISOR_TOKEN` environment variable and Home Assistant's internal API.*

## Development Conventions

- **Asynchronous I/O**: The project uses `asyncio` for the HTTP server and API clients. Maintain this pattern for any new features.
- **Configuration**: All runtime configuration is passed via a `config.json` file generated at startup by `run.sh`.
- **Logging**: Uses the standard `logging` module. In the context of Home Assistant, these logs are visible in the Add-on's "Log" tab.
- **Supervisor Integration**: Uses `bashio` for shell-based config parsing and follows the `hassio_api: true` requirement for communicating with the Home Assistant core.
