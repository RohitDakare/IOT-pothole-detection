import sqlite3
import time
import random
import os

DB_PATH = "d:/Rohit_imp_file/Project/IOT/IOT/raspi/lidar_readings.db"

def simulate_surroundings():
    print("Simulating Surroundings Scans...")
    
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS raw_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp REAL,
            distance_cm REAL,
            strength INTEGER,
            session_id TEXT
        )
    """)
    
    session_id = f"test_{int(time.time())}"
    
    # Generate 100 points simulating a road profile with a pothole in the middle
    for i in range(100):
        # Base depth is 20cm
        depth = 20.0
        
        # Pothole in the middle (points 40 to 60)
        if 40 < i < 60:
            depth += random.uniform(5, 15)
        else:
            depth += random.uniform(-1, 1)
            
        cursor.execute(
            "INSERT INTO raw_data (timestamp, distance_cm, strength, session_id) VALUES (?, ?, ?, ?)",
            (time.time() + (i * 0.05), depth, 1500, session_id)
        )
        conn.commit()
    
    conn.close()
    print(f"Simulation Data generated in {DB_PATH}")

if __name__ == "__main__":
    simulate_surroundings()
