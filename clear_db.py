import sqlite3
import os

DB_FILE = "d:/Rohit_imp_file/Project/IOT/IOT/backend/pothole_system.db"

def clear_db():
    if not os.path.exists(DB_FILE):
        print("Database file not found.")
        return
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM potholes")
    conn.commit()
    conn.close()
    print("Database cleared of mock data.")

if __name__ == "__main__":
    clear_db()
