import asyncio
import json
from wyoming.client import AsyncTcpClient
from wyoming.info import Describe

HA_IP = "homeassistant.local"
HA_PORT = 10400

async def main():
    print(f"Probing {HA_IP}:{HA_PORT}...")
    try:
        async with AsyncTcpClient(HA_IP, HA_PORT) as client:
            print("Connected. Waiting for 5 seconds without sending anything...")
            try:
                # Use a timeout to avoid hanging
                response = await asyncio.wait_for(client.read_event(), timeout=5.0)
                if response:
                    print(f"Received response type: {response.type}")
                    print(f"Response data: {response.data}")
                else:
                    print("Received None response (connection closed).")
            except asyncio.TimeoutError:
                print("No response (timeout). Connection still open?")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
