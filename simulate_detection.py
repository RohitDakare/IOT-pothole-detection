import requests
import time
import random
import datetime

API_URL = "http://34.93.53.7:8000/api/potholes"

def simulate_real_detection():
    # Simulate a variety of potholes over a "road section"
    print("Starting Full-Scale System Simulation...")
    
    detections = [
        {"lat": 28.9521, "lon": 77.1039, "depth": 5.0, "severity": "Moderate", "classification": "Major Pothole"},
        {"lat": 28.9525, "lon": 77.1044, "depth": 4.2, "severity": "Moderate", "classification": "Minor Pothole"},
        {"lat": 28.9528, "lon": 77.1049, "depth": 1.5, "severity": "Minor", "classification": "Normal Road (Dip)"}
    ]


    for det in detections:
        length = random.uniform(20.0, 50.0)
        width = length * 0.85
        data = {
            "latitude": det["lat"],
            "longitude": det["lon"],
            "depth": det["depth"],
            "length": length,
            "width": width,
            "severity": det["severity"],
            "classification": det[ "classification"],
            "timestamp": datetime.datetime.now().isoformat()
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
