import sqlite3
import os
from datetime import datetime

DB_PATH = "incidents/shieldeye.db"

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "CREATE TABLE IF NOT EXISTS incidents ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "timestamp TEXT NOT NULL, "
        "camera_id TEXT DEFAULT 'CAM_01', "
        "suspicion_score REAL NOT NULL, "
        "zone TEXT, behavior_tags TEXT, "
        "clip_path TEXT, thumbnail_path TEXT, "
        "is_false_alarm INTEGER DEFAULT 0)"
    )
    c.execute(
        "CREATE TABLE IF NOT EXISTS camera_health ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "camera_id TEXT, timestamp TEXT, status TEXT, message TEXT)"
    )
    conn.commit()
    conn.close()
    print(f"Database initialized: {DB_PATH}")

def log_incident(camera_id, score, zone, behavior_tags,
                 clip_path, thumbnail_path):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    tags = ", ".join(behavior_tags) if isinstance(behavior_tags, list) else behavior_tags
    c.execute(
        "INSERT INTO incidents "
        "(timestamp, camera_id, suspicion_score, zone, behavior_tags, "
        "clip_path, thumbnail_path) VALUES (?,?,?,?,?,?,?)",
        (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            camera_id, score, zone, tags, clip_path, thumbnail_path,
        )
    )
    incident_id = c.lastrowid
    conn.commit()
    conn.close()
    return incident_id

def mark_false_alarm(incident_id):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("UPDATE incidents SET is_false_alarm=1 WHERE id=?", (incident_id,))
    conn.commit()
    conn.close()

def get_incidents(limit=50, false_alarms=True):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    where = "" if false_alarms else "WHERE is_false_alarm=0"
    rows = conn.execute(
        f"SELECT * FROM incidents {where} ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def log_camera_health(camera_id, status, message):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO camera_health (camera_id,timestamp,status,message) VALUES(?,?,?,?)",
        (camera_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), status, message)
    )
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    iid = log_incident("CAM_01", 0.87, "Exit Zone", ["CONCEALMENT"],
                        "test_clip.avi", "test_thumb.jpg")
    print(f"Logged incident ID: {iid}")
    print(f"Total incidents: {len(get_incidents())}")
    print("Database OK!")