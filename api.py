"""
AegisAI - FastAPI Backend
Run: uvicorn api:app --reload --port 8000
"""

import os
import sys
import json
import sqlite3
import subprocess
import threading
from pathlib import Path
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# ── Config (FIX 2: Use absolute paths to eliminate DB/mismatch bugs) ──────
_BASE            = os.path.dirname(os.path.abspath(__file__))
DB_PATH          = os.path.join(_BASE, "incidents", "shieldeye.db")
CLIPS_DIR        = os.path.join(_BASE, "incidents", "clips")
SHOPLIFTING_DIR  = os.path.join(_BASE, "data", "Shoplifting_Class")
NORMAL_DIR       = os.path.join(_BASE, "data", "Normal_Class")
VIDEO_EXTS       = {".mp4", ".avi", ".mov", ".mkv"}

# Use the same Python interpreter that's running this API (i.e. the venv one)
PYTHON_EXE = sys.executable

# ── App ───────────────────────────────────────────────────────────────────
app = FastAPI(title="AegisAI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve clip files
os.makedirs(CLIPS_DIR, exist_ok=True)
app.mount("/clips", StaticFiles(directory=CLIPS_DIR), name="clips")

# ── DB helpers ────────────────────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def db_exists():
    return os.path.exists(DB_PATH)

# ── Batch run state ───────────────────────────────────────────────────────
batch_state = {
    "running": False,
    "total": 0,
    "done": 0,
    "current": "",
    "errors": [],
}

def get_processed_filenames() -> set:
    """Return set of source video basenames already logged in DB."""
    if not db_exists():
        return set()
    try:
        conn = sqlite3.connect(DB_PATH)
        rows = conn.execute("SELECT clip_path FROM incidents WHERE clip_path IS NOT NULL").fetchall()
        conn.close()
        return set(batch_state.get("processed_files", []))
    except Exception:
        return set()

def run_batch_job(video_paths: list[str]):
    batch_state["running"] = True
    batch_state["total"]   = len(video_paths)
    batch_state["done"]    = 0
    batch_state["errors"]  = []
    if "processed_files" not in batch_state:
        batch_state["processed_files"] = []

    for i, path in enumerate(video_paths):
        fname = os.path.basename(path)
        batch_state["current"] = fname
        try:
            # FIX 1 & 2a: Combined cwd validation with 300s deep learning execution headroom
            result = subprocess.run(
                [PYTHON_EXE, "inference.py",
                 "--source", path,
                 "--camera", f"CAM_{(i % 4) + 1:02d}",
                 "--no-preview"],
                capture_output=True,
                text=True,
                timeout=300,
                cwd=os.path.dirname(os.path.abspath(__file__)),
            )
            if result.returncode != 0:
                batch_state["errors"].append(
                    f"{fname}: {result.stderr[-300:]}"
                )
            else:
                # Mark as processed so next batch skips it
                batch_state["processed_files"].append(fname)
        except subprocess.TimeoutExpired:
            batch_state["errors"].append(f"{fname}: timeout")
        except Exception as e:
            batch_state["errors"].append(f"{fname}: {e}")

        batch_state["done"] = i + 1

    batch_state["running"] = False
    batch_state["current"] = ""

# ── Routes ────────────────────────────────────────────────────────────────

@app.get("/api/health")
def health():
    return {"status": "ok", "db": db_exists()}


@app.get("/api/incidents")
def get_incidents(limit: int = 50, include_false_alarms: bool = True):
    if not db_exists():
        return []
    conn = get_db()
    where = "" if include_false_alarms else "WHERE is_false_alarm = 0"
    rows = conn.execute(
        f"SELECT * FROM incidents {where} ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()

    result = []
    for r in rows:
        d = dict(r)
        tags_raw = d.get("behavior_tags") or ""
        d["behavior_tags"] = [t.strip() for t in tags_raw.split(",") if t.strip()]
        d["suspicion_score"] = round(float(d.get("suspicion_score", 0)), 4)
        d["incident_label"] = f"INC-{d['id']:03d}"
        result.append(d)
    return result


@app.get("/api/metrics")
def get_metrics():
    if not db_exists():
        return {"total": 0, "pending": 0, "verified": 0, "false_alarms": 0}
    conn = get_db()

    total       = conn.execute("SELECT COUNT(*) FROM incidents").fetchone()[0]
    false_alarms = conn.execute(
        "SELECT COUNT(*) FROM incidents WHERE is_false_alarm = 1"
    ).fetchone()[0]
    verified    = conn.execute(
        "SELECT COUNT(*) FROM incidents WHERE suspicion_score >= 0.7 AND is_false_alarm = 0"
    ).fetchone()[0]
    pending     = conn.execute(
        "SELECT COUNT(*) FROM incidents WHERE suspicion_score >= 0.55 AND suspicion_score < 0.7 AND is_false_alarm = 0"
    ).fetchone()[0]

    today = datetime.now().strftime("%Y-%m-%d")
    today_count = conn.execute(
        "SELECT COUNT(*) FROM incidents WHERE timestamp LIKE ?", (f"{today}%",)
    ).fetchone()[0]

    conn.close()
    return {
        "total":        total,
        "pending":      pending,
        "verified":     verified,
        "false_alarms": false_alarms,
        "today_delta":  today_count,
    }


@app.patch("/api/incidents/{incident_id}/false-alarm")
def mark_false_alarm(incident_id: int):
    if not db_exists():
        raise HTTPException(404, "Database not found")
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "UPDATE incidents SET is_false_alarm = 1 WHERE id = ?", (incident_id,)
    )
    conn.commit()
    conn.close()
    return {"ok": True}


@app.get("/api/incidents/{incident_id}/video")
def get_video(incident_id: int):
    if not db_exists():
        raise HTTPException(404, "Database not found")
    conn = get_db()
    row = conn.execute(
        "SELECT clip_path FROM incidents WHERE id = ?", (incident_id,)
    ).fetchone()
    conn.close()
    if not row or not row["clip_path"]:
        raise HTTPException(404, "No clip for this incident")
    path = row["clip_path"]
    if not os.path.exists(path):
        raise HTTPException(404, f"Clip file not found: {path}")
    
    # FIX 3: Dynamic video format streaming evaluation
    ext = os.path.splitext(path)[1].lower()
    media_type = "video/mp4" if ext == ".mp4" else "video/x-msvideo"
    return FileResponse(path, media_type=media_type)


@app.get("/api/videos/available")
def list_available_videos():
    """Return count of videos ready to batch-process."""
    videos = []
    for folder in [SHOPLIFTING_DIR, NORMAL_DIR]:
        if os.path.isdir(folder):
            for f in Path(folder).iterdir():
                if f.suffix.lower() in VIDEO_EXTS:
                    videos.append(str(f))
    return {"count": len(videos), "folders": {
        "shoplifting": os.path.isdir(SHOPLIFTING_DIR),
        "normal":      os.path.isdir(NORMAL_DIR),
    }}


@app.post("/api/batch-run")
def start_batch_run(background_tasks: BackgroundTasks, limit: int = 20):
    """Start batch inference on DCSASS videos (non-blocking). Skips already-processed files."""
    if batch_state["running"]:
        return {"ok": False, "message": "Batch already running"}

    already_done = set(batch_state.get("processed_files", []))

    shoplifting_videos = []
    normal_videos      = []
    for f in sorted(Path(SHOPLIFTING_DIR).iterdir()) if os.path.isdir(SHOPLIFTING_DIR) else []:
        if f.suffix.lower() in VIDEO_EXTS and f.name not in already_done:
            shoplifting_videos.append(str(f))
    for f in sorted(Path(NORMAL_DIR).iterdir()) if os.path.isdir(NORMAL_DIR) else []:
        if f.suffix.lower() in VIDEO_EXTS and f.name not in already_done:
            normal_videos.append(str(f))

    videos = []
    for s, n in zip(shoplifting_videos, normal_videos):
        videos.extend([s, n])
    longer = shoplifting_videos if len(shoplifting_videos) > len(normal_videos) else normal_videos
    videos.extend(longer[len(min(shoplifting_videos, normal_videos, key=len)):])

    videos = videos[:limit]

    if not videos:
        return {"ok": False, "message": "No new unprocessed videos found"}

    background_tasks.add_task(run_batch_job, videos)
    return {"ok": True, "queued": len(videos), "from_shoplifting": len(shoplifting_videos[:limit]), "from_normal": len(normal_videos[:limit])}


@app.get("/api/batch-status")
def batch_status():
    return {**batch_state}


@app.get("/api/report/generate")
def generate_report():
    """Trigger PDF report generation and return download path."""
    try:
        result = subprocess.run(
            [PYTHON_EXE, "report_generator.py"],
            capture_output=True, text=True, timeout=30,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        if result.returncode != 0:
            raise HTTPException(500, result.stderr)
        
        # FIX 4: Secure path lookups relative to parent project space
        for fname in [
            os.path.join(_BASE, "incidents", "daily_report.pdf"),
            os.path.join(_BASE, "daily_report.pdf"),
            "incidents/daily_report.pdf",
            "daily_report.pdf",
        ]:
            if os.path.exists(fname):
                return FileResponse(fname, media_type="application/pdf",
                                    filename=os.path.basename(fname))
        raise HTTPException(404, "Report file not found after generation")
    except subprocess.TimeoutExpired:
        raise HTTPException(500, "Report generation timed out")