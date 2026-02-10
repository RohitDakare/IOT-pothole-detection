import requests
import time
import math
import random
import uuid
import sys

# Configuration
SERVER_URL = "http://127.0.0.1:8000" # Default to localhost
if len(sys.argv) > 1:
    SERVER_URL = sys.argv[1]

API_ENDPOINT = f"{SERVER_URL}/api/road-profile"
SESSION_ID = str(uuid.uuid4())

print(f"🚀 Starting LiDAR Simulation")
print(f"📡 Target: {API_ENDPOINT}")
print(f"🔑 Session ID: {SESSION_ID}")
print("Press Ctrl+C to stop...")

start_time = time.time()
speed = 5.0 # virtual speed m/s

try:
    while True:
        # Generate a batch of 10 points (simulating 0.2s of data at 50Hz)
        batch = []
        for i in range(10):
            ts = time.time()
            elapsed = ts - start_time
            
            # Simulate Road Surface (Sine wave for 'bumpy' road)
            # Base height 0 + sine wave + noise
            distance_cm = (math.sin(elapsed * 2) * 2) + random.uniform(-0.5, 0.5)
            
            # Inject a "Pothole" every 5 seconds
            if int(elapsed) % 5 == 0 and (elapsed % 1.0) < 0.2:
                distance_cm += random.uniform(5, 12) # Deep pothole!
                
            # Z grows forward
            z = elapsed * speed
            
            # X oscillates slightly (driving lane weave)
            x = math.sin(elapsed * 0.5) * 5
            
            batch.append({
                "x": x,
                "y": distance_cm,
                "z": z
            })
            
            time.sleep(0.02) # 50Hz interval

        # Post batch
        try:
            resp = requests.post(API_ENDPOINT, json={
                "session_id": SESSION_ID,
                "points": batch
            }, timeout=1)
            
            if resp.status_code == 200:
                print(f"✅ Sent {len(batch)} points | Z: {batch[-1]['z']:.1f}m", end='\r')
            else:
                print(f"⚠️ Server Error: {resp.status_code}")
                
        except requests.exceptions.ConnectionError:
            print(f"❌ Connection Failed! Is backend running at {SERVER_URL}?")
            time.sleep(1)
            
except KeyboardInterrupt:
    print("\n🛑 Simulation Stopped.")
