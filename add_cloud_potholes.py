import requests
import datetime
import json
import socket
import time

# Cloud API Base URL Candidates
CLOUD_IPS = ["195.35.23.26"]
PORTS = [80, 8000, 8080, 3000, 5000, 443]

def check_port(ip, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    result = sock.connect_ex((ip, port))
    sock.close()
    return result == 0

def add_pothole(base_url, lat, lon, depth, length, width):
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
        print(f"Attempting to POST to {base_url}...")
        response = requests.post(base_url, json=payload, timeout=5)
        if response.status_code == 200:
            print(f"✅ SUCCESS! Added pothole at {lat}, {lon}. Response: {response.json()}")
            return True
        else:
            print(f"❌ Failed. Status: {response.status_code}, Response: {response.text}")
    except Exception as e:
        print(f"❌ Error connecting to {base_url}: {e}")
    return False

def main():
    detected_url = None
    print("🔍 Scanning cloud server ports...")
    
    open_ports = []
    for ip in CLOUD_IPS:
        for port in PORTS:
            if check_port(ip, port):
                print(f"✅ Port {port} is OPEN on {ip}")
                open_ports.append((ip, port))
    
    if not open_ports:
        print("❌ No open ports found on cloud server.")
        return

    # Try all open ports
    success = False
    for ip, port in open_ports:
        # Construct URL
        if port == 80:
            url = f"http://{ip}/api/potholes"
        elif port == 443:
            url = f"https://{ip}/api/potholes"
        else:
            url = f"http://{ip}:{port}/api/potholes"
        
        print(f"\n🚀 Trying Target URL: {url}")
        
        # Try both potholes
        r1 = add_pothole(url, 19.0765, 72.8780, 5.0, 7.0, 7.0)
        r2 = add_pothole(url, 19.0755, 72.8770, 5.0, 7.0, 7.0)
        
        if r1 or r2:
            print(f"🎉 Success using {url}!")
            success = True
            break
            
    if not success:
        print("\n❌ Could not upload data to any open port on the cloud server.")

if __name__ == "__main__":
    main()
