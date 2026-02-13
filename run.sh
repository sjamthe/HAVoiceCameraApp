#!/usr/bin/with-contenv bashio

# Get configuration from Home Assistant
IPWEBCAM_HOST=$(bashio::config 'ipwebcam_host')
IPWEBCAM_PORT=$(bashio::config 'ipwebcam_port')
GEMINI_API_KEY=$(bashio::config 'gemini_api_key')
GEMINI_MODEL=$(bashio::config 'gemini_model')

# Get Home Assistant token from supervisor
SUPERVISOR_TOKEN="${SUPERVISOR_TOKEN}"

bashio::log.info "Starting Voice Camera Assistant..."
bashio::log.info "IP Webcam: ${IPWEBCAM_HOST}:${IPWEBCAM_PORT}"
bashio::log.info "Gemini Model: ${GEMINI_MODEL}"

# Create config file
cat > /config.json << EOF
{
  "ipwebcam_host": "${IPWEBCAM_HOST}",
  "ipwebcam_port": ${IPWEBCAM_PORT},
  "ha_host": "supervisor",
  "ha_port": 80,
  "ha_token": "${SUPERVISOR_TOKEN}",
  "gemini_api_key": "${GEMINI_API_KEY}",
  "gemini_model": "${GEMINI_MODEL}",
  "http_port": 8099
}
EOF

# Run the Python script
exec python3 /voice_camera_assistant.py --config /config.json
