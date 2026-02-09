import sqlite3
import time
import requests
import json
import math

# =================================================================
# LiDAR Spatial Analyzer (Surroundings & Road Profile)
# This script processes raw LiDAR depth readings into a spatial 
# coordinate stream for the 3D Dashboard.
# =================================================================

BACKEND_URL = "http://localhost:8000/api/road-profile"
DB_PATH = "d:/Rohit_imp_file/Project/IOT/IOT/raspi/lidar_readings.db"

class LidarSpatialAnalyzer:
    def __init__(self, speed_mps=0.3):
        self.speed = speed_mps  # Estimated robot speed in meters per second
        self.last_sync_time = time.time()
        self.processed_ids = []

    def get_new_readings(self):
        """Fetch un-processed readings from the local database."""
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Fetch last 50 readings for a mini-batch update
            cursor.execute("SELECT * FROM raw_data ORDER BY id DESC LIMIT 50")
            rows = cursor.fetchall()
            conn.close()
            return rows
        except Exception as e:
            print(f"DB Error: {e}")
            return []

    def process_and_sync(self):
        print("LiDAR Analyzer: Starting real-time spatial reconstruction...")
        
        while True:
            rows = self.get_new_readings()
            if not rows:
                time.sleep(1)
                continue

            points = []
            start_ts = rows[-1]['timestamp']
            
            for row in rows:
                # Delta time from the start of this batch
                dt = row['timestamp'] - start_ts
                
                # Spatial Reconstruction Logic:
                # X = Longitudinal distance (based on vehicle speed)
                # Y = Vertical Depth (measured distance)
                # Z = Lateral (since it's a fixed point LiDAR, we assume center)
                
                x = dt * self.speed * 100 # Convert to cm
                y = row['distance_cm']
                points.append({
                    "x": round(x, 2),
                    "y": round(y, 2),
                    "z": 0,
                    "strength": row['strength']
                })

            # Sync with Backend
            payload = {
                "session_id": rows[0]['session_id'],
                "points": points
            }
            
            try:
                res = requests.post(BACKEND_URL, json=payload, timeout=2)
                if res.status_code == 200:
                    print(f"Synced {len(points)} road profile points to Dashboard.")
            except Exception as e:
                print(f"Sync Error: {e}")

            time.sleep(0.5) # Update frequency for dashboard smoothness

if __name__ == "__main__":
    analyzer = LidarSpatialAnalyzer()
    analyzer.process_and_sync()
