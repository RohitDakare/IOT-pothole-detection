import requests
import time

API_URL = "http://localhost:8000/api/potholes"

def send(lat, lon, depth, msg):
    print(f"\n--- {msg} ---")
    data = {
        "latitude": lat,
        "longitude": lon,
        "depth": depth,
        "length": 30.0,
        "severity": "Unknown", 
        "timestamp": time.time()
    }
    try:
        res = requests.post(API_URL, json=data)
        print(f"Response: {res.json()}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Wait for server
    time.sleep(2)
    
    # 1. New Deep Pothole (> 8cm) -> Should be RED
    send(19.0760, 72.8777, 12.5, "Detecting Deep Pothole (12.5cm)")
    
    # 2. New Shallow Pothole (<= 8cm) -> Should be ORANGE
    send(19.0800, 72.8850, 6.4, "Detecting Moderate Pothole (6.4cm)")
    
    # 3. Re-scanning Deep Pothole location with < 2cm -> Should be GREEN (Repaired)
    send(19.0760, 72.8777, 1.2, "Re-scanning Deep Pothole location (1.2cm - Repaired)")
