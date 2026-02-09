import sqlite3
import time
import serial
import threading
from datetime import datetime

# =================================================================
# High-Speed LiDAR Data Recorder
# This script reads raw TF02-Pro data and saves it to a dedicated DB
# for 3D Road Mapping and Analysis.
# =================================================================

class LidarDatabase:
    def __init__(self, db_path="lidar_readings.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.init_db()

    def init_db(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS raw_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL,
                distance_cm REAL,
                strength INTEGER,
                session_id TEXT
            )
        """)
        self.conn.commit()

    def save_reading(self, distance, strength, session_id):
        self.cursor.execute(
            "INSERT INTO raw_data (timestamp, distance_cm, strength, session_id) VALUES (?, ?, ?, ?)",
            (time.time(), distance, strength, session_id)
        )
        self.conn.commit()

class LidarRecorder:
    def __init__(self, port="/dev/ttyAMA5", baud=115200):
        self.port = port
        self.baud = baud
        self.db = LidarDatabase()
        self.running = False
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    def start(self):
        self.running = True
        try:
            ser = serial.Serial(self.port, self.baud, timeout=1)
            print(f"LiDAR Recorder Started on {self.port} (Session: {self.session_id})")
            
            while self.running:
                if ser.in_waiting >= 9:
                    res = ser.read(9)
                    if res[0] == 0x59 and res[1] == 0x59: # Header
                        distance = res[2] + res[3] * 256
                        strength = res[4] + res[5] * 256
                        
                        # Save to Database
                        self.db.save_reading(distance, strength, self.session_id)
                        
                        # Optional: Print every 20th reading to console (prevent flooding)
                        if int(time.time() * 100) % 20 == 0:
                            print(f"Captured: {distance} cm | Strength: {strength}")
                
                time.sleep(0.01) # 100Hz capture freq
        except Exception as e:
            print(f"LiDAR Recorder Error: {e}")
        finally:
            self.running = False
            if 'ser' in locals(): ser.close()

    def stop(self):
        self.running = False

if __name__ == "__main__":
    recorder = LidarRecorder()
    try:
        recorder.start()
    except KeyboardInterrupt:
        print("\nStopping LiDAR Recorder...")
        recorder.stop()
