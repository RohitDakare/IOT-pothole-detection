import requests
import time
import random

API_URL = "http://localhost:8000/api/potholes"

def send_mock_pothole():
    # Lat/Lon near Mumbai for demonstration
    lat = 19.0760 + (random.random() - 0.5) * 0.01
    lon = 72.8777 + (random.random() - 0.5) * 0.01
    depth = round(random.uniform(2.0, 15.0), 2)
    
    if depth > 7:
        severity = "Critical"
    elif depth > 3:
        severity = "Moderate"
    else:
        severity = "Minor"

    data = {
        "latitude": lat,
        "longitude": lon,
        "depth": depth,
        "severity": severity,
        "timestamp": time.time()
    }

    try:
        response = requests.post(API_URL, json=data)
        if response.status_code == 200:
            print(f"Success! Detected {severity} pothole at {lat}, {lon} (Depth: {depth}cm)")
        else:
            print(f"Failed to send data: {response.text}")
    except Exception as e:
        print(f"Error connecting to server: {e}. (Is the backend running?)")

if __name__ == "__main__":
    print("Simulating pothole detections... Press Ctrl+C to stop.")
    while True:
        send_mock_pothole()
        time.sleep(10) # Send every 10 seconds
