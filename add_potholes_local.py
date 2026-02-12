import sqlite3
import datetime
import json

DB_FILE = 'backend/pothole_system.db'

def insert_pothole(lat, lon, depth, length, width):
    volume = length * width * depth
    severity = "Moderate"
    status = "Orange"
    if depth > 8:
        severity = "Critical"
        status = "Red"
    elif depth < 2:
        severity = "Minor"
        status = "Green"

    profile_data = json.dumps([])
    detected_at = datetime.datetime.now()

    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        query = """
        INSERT INTO potholes (latitude, longitude, depth, length, width, volume, profile_data, severity_level, status, detected_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        cursor.execute(query, (
            lat, lon, depth, length, width, volume, profile_data, severity, status, detected_at
        ))
        conn.commit()
        print(f"Added pothole at {lat}, {lon} with ID: {cursor.lastrowid}")
        conn.close()
    except Exception as e:
        print(f"Error inserting pothole: {e}")

# Pothole 1
insert_pothole(19.0765, 72.8780, 5.0, 7.0, 7.0)

# Pothole 2
insert_pothole(19.0755, 72.8770, 5.0, 7.0, 7.0)
