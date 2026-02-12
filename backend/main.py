from fastapi import FastAPI, UploadFile, File, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from datetime import datetime
import sqlite3
import os
import uuid
import json
from geopy.geocoders import Nominatim
from typing import List, Dict, Any

app = FastAPI(title="Smart Pothole Detection API (SQLite Mode)")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_FILE = "pothole_system.db"
UPLOAD_DIR = "uploads"
LIDAR_UPLOAD_DIR = "lidar_scans"

if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)
if not os.path.exists(LIDAR_UPLOAD_DIR):
    os.makedirs(LIDAR_UPLOAD_DIR)

active_websockets: List[WebSocket] = []

# Initialize Database
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Create valid table with new schema
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS potholes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        latitude REAL,
        longitude REAL,
        depth REAL,
        length REAL DEFAULT 0,
        width REAL DEFAULT 0,
        severity_level TEXT,
        image_url TEXT,
        status TEXT DEFAULT 'Red',
        detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        repaired_at TIMESTAMP NULL
    )
    """)

    # High-density road data for 3D mapping
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS road_profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT,
        points_json TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    
    # Attempt migration for existing databases
    try:
        cursor.execute("ALTER TABLE potholes ADD COLUMN length REAL DEFAULT 0")
    except: pass
    try:
        cursor.execute("ALTER TABLE potholes ADD COLUMN width REAL DEFAULT 0")
    except: pass
    try:
        cursor.execute("ALTER TABLE potholes ADD COLUMN lidar_scan_url TEXT NULL")
    except: pass

    conn.commit()
    conn.close()


init_db()

@app.websocket("/ws/potholes")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_websockets.append(websocket)
    try:
        while True:
            # We don't expect to receive messages from the dashboard,
            # but we need to keep the connection alive.
            # You could add logic here to handle messages if needed.
            await websocket.receive_text() 
    except WebSocketDisconnect:
        active_websockets.remove(websocket)
        print("WebSocket disconnected")

class PotholeData(BaseModel):
    latitude: float
    longitude: float
    depth: float
    length: float = 0.0
    width: float = 0.0
    volume: float = 0.0
    profile: List[float] = []  # Raw depth points
    severity: str
    timestamp: str 

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row 
    return conn

# Ensure new columns exist
def upgrade_db_schema():
    conn = get_db_connection()
    try:
        conn.execute("ALTER TABLE potholes ADD COLUMN volume REAL DEFAULT 0")
    except: pass
    try:
        conn.execute("ALTER TABLE potholes ADD COLUMN profile_data TEXT DEFAULT '[]'")
    except: pass
    conn.commit()
    conn.close()

upgrade_db_schema()

@app.post("/api/potholes")
async def report_pothole(data: PotholeData):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. Check for nearby existing potholes
        threshold_dist = 0.00005 
        cursor.execute("""
            SELECT id, depth, status FROM potholes 
            WHERE ABS(latitude - ?) < ? AND ABS(longitude - ?) < ?
            ORDER BY detected_at DESC LIMIT 1
        """, (data.latitude, threshold_dist, data.longitude, threshold_dist))
        
        existing = cursor.fetchone()
        
        # Logic for Color/Status based on Depth
        if data.depth > 8:
            new_status = 'Red'
            new_severity = 'Critical'
        elif data.depth < 2.0:
            new_status = 'Green'
            new_severity = 'Minor'
        else:
            new_status = 'Orange'
            new_severity = 'Moderate'

        if existing:
            # 2. Repair Logic (Mark existing as Green if current depth is low)
            if data.depth < 2.0:
                cursor.execute("""
                    UPDATE potholes SET status = 'Green', repaired_at = ? 
                    WHERE id = ?
                """, (datetime.now(), existing['id']))
                conn.commit()
                conn.close()
                return {"status": "repaired", "id": existing['id']}
            
        # 3. Insert New Pothole with Profile Data
        query = """
        INSERT INTO potholes (latitude, longitude, depth, length, width, volume, profile_data, severity_level, status, detected_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        # Parse timestamp string to datetime object if needed, or store as is if SQLite handles it
        # Ideally, we convert ISO string back to datetime for storage consistency
        try:
            dt_object = datetime.fromisoformat(data.timestamp)
        except:
            dt_object = datetime.now()

        cursor.execute(query, (
            data.latitude, 
            data.longitude, 
            data.depth, 
            data.length, 
            data.width,
            data.volume,
            json.dumps(data.profile), # Serialize profile list
            new_severity, 
            new_status,
            dt_object
        ))
        conn.commit()
        pothole_id = cursor.lastrowid
        
        # Broadcast via WebSocket
        cursor.execute("SELECT * FROM potholes WHERE id = ?", (pothole_id,))
        new_pothole = cursor.fetchone()
        conn.close()

        if new_pothole:
            pothole_dict = dict(new_pothole)
            for websocket in active_websockets:
                try:
                    await websocket.send_json(pothole_dict)
                except:
                    active_websockets.remove(websocket)

        return {"status": "success", "id": pothole_id}
    except Exception as e:
        print(f"Error saving pothole: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload_image")
async def upload_image(file: UploadFile = File(...)):
    try:
        file_name = f"{uuid.uuid4()}.jpg"
        file_path = os.path.join(UPLOAD_DIR, file_name)
        
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())
            
        conn = get_db_connection()
        cursor = conn.cursor()
        # Correlate with last pothole
        cursor.execute("UPDATE potholes SET image_url = ? WHERE id = (SELECT MAX(id) FROM potholes)", (f"/uploads/{file_name}",))
        conn.commit()
        conn.close()
        
        return {"status": "success", "url": f"/uploads/{file_name}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/potholes/{pothole_id}/lidar_scan")
async def upload_lidar_scan(pothole_id: int, file: UploadFile = File(...)):
    try:
        # Check if pothole exists
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM potholes WHERE id = ?", (pothole_id,))
        pothole_exists = cursor.fetchone()
        if not pothole_exists:
            conn.close()
            raise HTTPException(status_code=404, detail=f"Pothole with ID {pothole_id} not found.")

        # Save the LiDAR file
        # Use original filename as a base, but ensure uniqueness
        original_filename = file.filename
        file_extension = os.path.splitext(original_filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(LIDAR_UPLOAD_DIR, unique_filename)
        
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())
            
        lidar_scan_url = f"/{LIDAR_UPLOAD_DIR}/{unique_filename}"
        
        # Update the database
        cursor.execute("UPDATE potholes SET lidar_scan_url = ? WHERE id = ?", (lidar_scan_url, pothole_id))
        conn.commit()
        conn.close()
        
        return {"status": "success", "url": lidar_scan_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/potholes/stats")
async def get_pothole_stats():
    # ... existing stats logic ...
    return {"total": 0} # Placeholder



class RoadProfile(BaseModel):
    session_id: str
    points: List[Dict[str, float]]  # List of {x, y, z}

@app.post("/api/road-profile")
async def upload_road_profile(data: RoadProfile):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO road_profiles (session_id, points_json) VALUES (?, ?)", 
                      (data.session_id, json.dumps(data.points)))
        conn.commit()
        conn.close()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/road-profile")
async def get_road_profile():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # Get last 100 batches of points (approx 1-2 minutes of history)
        cursor.execute("SELECT points_json FROM road_profiles ORDER BY id DESC LIMIT 100")
        rows = cursor.fetchall()
        conn.close()
        
        all_points = []
        for row in rows:
            try:
                points = json.loads(row['points_json'])
                # Just append if it's a list
                if isinstance(points, list):
                    all_points.extend(points)
            except: pass
            
        return all_points
    except Exception as e:
        print(f"Error fetching profile: {e}")
        return []

@app.get("/api/potholes")
async def get_potholes():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM potholes ORDER BY detected_at DESC")
    rows = cursor.fetchall()
    conn.close()
    
    geolocator = Nominatim(user_agent="pothole-detector")
    results = []
    for row in rows:
        pothole_data = dict(row)
        try:
            location = geolocator.reverse((pothole_data['latitude'], pothole_data['longitude']), exactly_one=True)
            pothole_data['address'] = location.address if location else "Address not found"
        except Exception as e:
            pothole_data['address'] = "Error fetching address"

        results.append(pothole_data)
        
    return JSONResponse(content=results)

@app.put("/api/potholes/{pothole_id}/repair")
async def repair_pothole(pothole_id: int):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = "UPDATE potholes SET status = 'Green', repaired_at = ? WHERE id = ?"
        cursor.execute(query, (datetime.utcnow(), pothole_id))
        conn.commit()
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Pothole not found")
            
        conn.close()
        return {"status": "success", "message": f"Pothole {pothole_id} marked as repaired."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Serve the uploaded images
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.mount("/lidar_scans", StaticFiles(directory="lidar_scans"), name="lidar_scans")

# Serve the Dashboard
if os.path.exists("../dashboard"):
    app.mount("/static", StaticFiles(directory="../dashboard"), name="static")
    @app.get("/")
    async def get_index():
        from fastapi.responses import FileResponse
        return FileResponse("../dashboard/index.html")
    @app.get("/3d-map")
    async def get_3d_map():
        from fastapi.responses import FileResponse
        return FileResponse("../dashboard/3d_map.html")
    @app.get("/kg/admin")
    async def get_admin_page():
        from fastapi.responses import FileResponse
        return FileResponse("../dashboard/admin.html")
elif os.path.exists("dashboard"):
    app.mount("/static", StaticFiles(directory="dashboard"), name="static")
    @app.get("/")
    async def get_index():
        from fastapi.responses import FileResponse
        return FileResponse("dashboard/index.html")
    @app.get("/3d-map")
    async def get_3d_map():
        from fastapi.responses import FileResponse
        return FileResponse("dashboard/3d_map.html")
    @app.get("/kg/admin")
    async def get_admin_page():
        from fastapi.responses import FileResponse
        return FileResponse("dashboard/admin.html")

@app.post("/api/admin/seed")
async def seed_test_potholes():
    # Logic from add_potholes_remote.py
    potholes_to_add = [
        {"lat": 28.9521, "lon": 77.1039, "depth": 5.0, "length": 7.0, "width": 7.0},
        {"lat": 28.9525, "lon": 77.1045, "depth": 5.0, "length": 7.0, "width": 7.0}
    ]
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    added = []
    try:
        for p in potholes_to_add:
            # Calculate volume
            volume = p['length'] * p['width'] * p['depth']
            
            # Determine severity (simplified logic matches script intent)
            severity = "Moderate"
            status = "Orange" # Depth 5.0 is moderate
            
            query = """
            INSERT INTO potholes (latitude, longitude, depth, length, width, volume, profile_data, severity_level, status, detected_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            cursor.execute(query, (
                p['lat'], p['lon'], p['depth'], p['length'], p['width'], 
                volume, "[]", severity, status, datetime.now()
            ))
            added.append(cursor.lastrowid)
            
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()
        
    return {"status": "success", "message": f"Added {len(added)} test potholes", "ids": added}

@app.delete("/api/potholes/{pothole_id}")
async def delete_pothole(pothole_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM potholes WHERE id = ?", (pothole_id,))
    conn.commit()
    
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Pothole not found")
        
    conn.close()
    return {"status": "success", "message": f"Pothole {pothole_id} deleted"}

@app.delete("/api/potholes")
async def delete_all_potholes():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM potholes")
    conn.commit()
    conn.close()
    return {"status": "success", "message": "All potholes deleted"}

if __name__ == "__main__":
    import uvicorn
    print(f"Server starting. Database: {DB_FILE}")
    print("Dashboard: http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
