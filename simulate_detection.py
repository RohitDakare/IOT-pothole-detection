import requests
import time
import random

API_URL = "http://localhost:8000/api/potholes"

def simulate_real_detection():
    # Simulate a variety of potholes over a "road section"
    print("Starting Full-Scale System Simulation...")
    
    detections = [
        {"lat": 19.0760, "lon": 72.8777, "depth": 10.5, "severity": "Critical", "classification": "Major Pothole"},
        {"lat": 19.0765, "lon": 72.8780, "depth": 4.2, "severity": "Moderate", "classification": "Minor Pothole"},
        {"lat": 19.0770, "lon": 72.8785, "depth": 1.5, "severity": "Minor", "classification": "Normal Road (Dip)"}
    ]

    for det in detections:
        data = {
            "latitude": det["lat"],
            "longitude": det["lon"],
            "depth": det["depth"],
            "length": random.uniform(20.0, 50.0),
            "width": 0.0,
            "severity": det["severity"],
            "classification": det[ "classification"],
            "timestamp": time.time()
        }
        
        try:
            res = requests.post(API_URL, json=data)
            if res.status_code == 200:
                print(f"Verified: {det['severity']} Pothole mapped at {det['lat']}, {det['lon']}")
            else:
                print(f"Error: {res.text}")
        except:
            print("Backend not reachable. Ensure main.py is running.")
        
        time.sleep(2)

if __name__ == "__main__":
    simulate_real_detection()
