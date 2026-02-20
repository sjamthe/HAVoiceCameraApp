import socket
import time

HA_IP = "homeassistant.local"
HA_PORT = 10400

try:
    print(f"Connecting to {HA_IP}:{HA_PORT}...")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HA_IP, HA_PORT))
    print("Connected. Waiting 5 seconds...")
    time.sleep(5)
    print("Sending something...")
    s.sendall(b'{"type": "describe", "data": {}}\n')
    print("Sent. Waiting for response...")
    data = s.recv(1024)
    if data:
        print(f"Received: {data.decode()}")
    else:
        print("Received EOF.")
except Exception as e:
    print(f"Error: {e}")
finally:
    s.close()
