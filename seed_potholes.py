import requests
import datetime
import json

# Cloud API Base URL
BASE_URL = "http://127.0.0.1:8000/api/potholes"

def add_pothole(lat, lon, depth, length, width):
    volume = length * width * depth
    payload = {
        "latitude": lat,
        "longitude": lon,
        "depth": depth,
        "length": length,
        "width": width,
        "volume": volume,
        "profile": [],
        "severity": "Moderate", # Will be recalculated by backend but required by schema
        "timestamp": datetime.datetime.now().isoformat()
    }
    
    try:
        response = requests.post(BASE_URL, json=payload)
        if response.status_code == 200:
            print(f"Successfully added pothole at {lat}, {lon}. Response: {response.json()}")
        else:
            print(f"Failed to add pothole at {lat}, {lon}. Status: {response.status_code}, Response: {response.text}")
    except Exception as e:
        print(f"Error connecting to cloud API: {e}")

# Pothole 1
add_pothole(19.0765, 72.8780, 5.0, 7.0, 7.0)

# Pothole 2
add_pothole(19.0755, 72.8770, 5.0, 7.0, 7.0)
