import requests
import datetime
import json

# GCP Cloud API URL
# User provided: 34.93.53.7:8000/api/pothole
# Corrected to plural based on backend code: /api/potholes
BASE_URL = "http://34.93.53.7:8000/api/potholes"

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
        "severity": "Moderate", 
        "timestamp": datetime.datetime.now().isoformat()
    }
    
    try:
        print(f"🚀 Sending data to {BASE_URL}...")
        response = requests.post(BASE_URL, json=payload, timeout=10)
        if response.status_code == 200:
            print(f"✅ SUCCESS! Added pothole at {lat}, {lon}.")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ FAILED. Status: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ CONNECTION ERROR: {e}")
        print("   Please check ensures port 8000 is open in GCP Firewall settings.")

if __name__ == "__main__":
    # Pothole 1
    add_pothole(19.0765, 72.8780, 5.0, 7.0, 7.0)

    # Pothole 2
    add_pothole(19.0755, 72.8770, 5.0, 7.0, 7.0)
