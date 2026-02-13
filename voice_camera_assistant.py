#!/usr/bin/env python3
"""
Voice-activated Camera Assistant for Home Assistant
Uses Home Assistant REST API and automations for triggering.
Captures camera snapshots and sends to Gemini for AI analysis.
"""

import asyncio
import aiohttp
from aiohttp import web
import logging
import json
import base64
import signal

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class VoiceCameraAssistant:
    def __init__(self, config):
        self.config = config
        self.app = None
        self.runner = None
        self.should_stop = False
        self.last_processed_time = 0
        
    async def capture_camera_snapshot(self):
        """Capture a snapshot from IP Webcam camera"""
        snapshot_url = f"http://{self.config['ipwebcam_host']}:{self.config['ipwebcam_port']}/shot.jpg"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(snapshot_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        image_data = await response.read()
                        logger.info(f"✓ Captured snapshot ({len(image_data)} bytes)")
                        return image_data
                    else:
                        logger.error(f"Failed to capture snapshot: {response.status}")
                        return None
        except asyncio.TimeoutError:
            logger.error("Timeout capturing snapshot")
            return None
        except Exception as e:
            logger.error(f"Error capturing snapshot: {e}")
            return None
    
    async def send_to_gemini(self, text, image_data=None):
        """Send text and optional image to Gemini API"""
        model = self.config.get('gemini_model', 'gemini-1.5-flash')
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.config['gemini_api_key']}"
        
        parts = [{"text": text}]
        
        if image_data:
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            parts.append({
                "inline_data": {
                    "mime_type": "image/jpeg",
                    "data": image_base64
                }
            })
        
        payload = {
            "contents": [{
                "parts": parts
            }]
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        result = await response.json()
                        response_text = result['candidates'][0]['content']['parts'][0]['text']
                        logger.info(f"✓ Gemini response received ({len(response_text)} chars)")
                        return response_text
                    else:
                        error_text = await response.text()
                        logger.error(f"Gemini API error {response.status}: {error_text}")
                        return None
        except asyncio.TimeoutError:
            logger.error("Gemini API request timed out")
            return None
        except Exception as e:
            logger.error(f"Error calling Gemini: {e}")
            return None
    
    async def notify_homeassistant(self, message, title="Voice Camera Assistant"):
        """Send notification to Home Assistant"""
        url = f"http://{self.config['ha_host']}:{self.config['ha_port']}/api/services/notify/persistent_notification"
        headers = {
            "Authorization": f"Bearer {self.config['ha_token']}",
            "Content-Type": "application/json"
        }
        payload = {
            "message": message,
            "title": title
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        logger.info("✓ Notification sent to Home Assistant")
                        return True
                    else:
                        error = await response.text()
                        logger.error(f"Failed to send notification ({response.status}): {error}")
                        return False
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
            return False
    
    async def process_voice_command(self, prompt=None):
        """Process voice command with camera snapshot"""
        logger.info("\n" + "="*50)
        logger.info("🎤 Processing voice command...")
        logger.info("="*50)
        
        # Capture camera snapshot
        image_data = await self.capture_camera_snapshot()
        
        if not image_data:
            await self.notify_homeassistant("Failed to capture image from camera", "Camera Error")
            return {"error": "Failed to capture image"}
        
        # Use provided prompt or default
        if not prompt:
            prompt = "Describe what you see in this image in detail"
        
        logger.info(f"📝 Prompt: {prompt}")
        
        # Send to Gemini
        response = await self.send_to_gemini(prompt, image_data)
        
        if response:
            await self.notify_homeassistant(
                f"**Question:** {prompt}\n\n**Answer:** {response}",
                "🤖 Camera AI Response"
            )
            logger.info("✓ Processing complete!")
            logger.info("="*50 + "\n")
            return {"success": True, "response": response}
        else:
            await self.notify_homeassistant("Failed to get response from Gemini AI", "AI Error")
            return {"error": "Failed to get Gemini response"}
    
    async def handle_trigger(self, request):
        """HTTP endpoint to manually trigger processing"""
        try:
            data = await request.json() if request.content_type == 'application/json' else {}
            prompt = data.get('prompt', None)
            
            logger.info("🔔 Trigger received via HTTP")
            result = await self.process_voice_command(prompt)
            
            return web.json_response(result)
        except Exception as e:
            logger.error(f"Error handling trigger: {e}")
            return web.json_response({"error": str(e)}, status=500)
    
    async def handle_health(self, request):
        """Health check endpoint"""
        return web.json_response({
            "status": "running",
            "ipwebcam": f"{self.config['ipwebcam_host']}:{self.config['ipwebcam_port']}",
            "gemini_model": self.config.get('gemini_model', 'gemini-1.5-flash'),
            "mode": "http_trigger"
        })
    
    async def start_http_server(self):
        """Start HTTP server for triggers"""
        self.app = web.Application()
        self.app.router.add_post('/trigger', self.handle_trigger)
        self.app.router.add_get('/health', self.handle_health)
        
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        
        port = self.config.get('http_port', 8099)
        site = web.TCPSite(self.runner, '0.0.0.0', port)
        await site.start()
        
        logger.info(f"✓ HTTP server started on port {port}")
        logger.info(f"  Trigger: POST http://local-voice-camera-assistant:{port}/trigger")
        logger.info(f"  Health:  GET  http://local-voice-camera-assistant:{port}/health")
    
    async def run(self):
        """Main run loop"""
        logger.info("\n" + "="*70)
        logger.info("🚀 Voice Camera Assistant Starting (HTTP Trigger Mode)")
        logger.info("="*70)
        logger.info(f"📱 IP Webcam: {self.config['ipwebcam_host']}:{self.config['ipwebcam_port']}")
        logger.info(f"🏠 Home Assistant: {self.config['ha_host']}:{self.config['ha_port']}")
        logger.info(f"🤖 Gemini Model: {self.config.get('gemini_model', 'gemini-1.5-flash')}")
        logger.info("="*70)
        logger.info("")
        logger.info("📋 How to use:")
        logger.info("")
        logger.info("  METHOD 1: Voice Commands via Home Assistant Automation")
        logger.info("  -------------------------------------------------------")
        logger.info("  1. Create automation in Home Assistant (see setup guide)")
        logger.info("  2. Say: 'Hey Assistant, camera what do you see?'")
        logger.info("  3. Automation calls this add-on's /trigger endpoint")
        logger.info("")
        logger.info("  METHOD 2: Manual HTTP Trigger")
        logger.info("  ------------------------------")
        logger.info("  curl -X POST http://local-voice-camera-assistant:8099/trigger \\")
        logger.info("    -H 'Content-Type: application/json' \\")
        logger.info("    -d '{\"prompt\": \"What do you see?\"}'")
        logger.info("")
        logger.info("  METHOD 3: Home Assistant Dashboard Button")
        logger.info("  ------------------------------------------")
        logger.info("  Add button card that calls rest_command service")
        logger.info("")
        logger.info("="*70 + "\n")
        
        # Start HTTP server
        await self.start_http_server()
        
        logger.info("✅ Assistant ready and waiting for triggers!\n")
        
        try:
            # Keep running indefinitely
            while not self.should_stop:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            logger.info("Shutting down...")
        finally:
            if self.runner:
                await self.runner.cleanup()
    
    async def shutdown(self):
        """Cleanup on shutdown"""
        logger.info("Cleaning up...")
        self.should_stop = True
        if self.runner:
            await self.runner.cleanup()


def load_config(config_file):
    """Load configuration from file"""
    try:
        with open(config_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Config file not found: {config_file}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in config file: {e}")
        return None


async def main():
    import argparse
    parser = argparse.ArgumentParser(description='Voice Camera Assistant for Home Assistant')
    parser.add_argument('--config', default='config.json', help='Configuration file path')
    args = parser.parse_args()
    
    config = load_config(args.config)
    if not config:
        logger.error("Failed to load configuration")
        return
    
    assistant = VoiceCameraAssistant(config)
    
    # Handle shutdown signals
    loop = asyncio.get_event_loop()
    
    def signal_handler():
        logger.info("\nReceived shutdown signal")
        asyncio.create_task(assistant.shutdown())
        loop.stop()
    
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, signal_handler)
    
    try:
        await assistant.run()
    except Exception as e:
        logger.error(f"Error in main: {e}")
        import traceback
        traceback.print_exc()
        await assistant.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
