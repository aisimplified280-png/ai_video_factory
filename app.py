"""AI SIMPLIFIED LAB — Video Factory Web UI. Run: python app.py (nothing else needed).

Generation runs in a background thread so the page never freezes.
The page polls /api/job/<id> every 2s for live progress and auto-refreshes
the recent-videos list when the render finishes.
"""
from __future__ import annotations

import envfile
envfile.load_dotenv()

import json
import os
import subprocess
import sys
import threading
import traceback
import uuid
from datetime import datetime
from pathlib import Path
import re

from flask import Flask, abort, jsonify, redirect, render_template, request, send_from_directory, url_for

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "output"
app = Flask(__name__)

# ── Job registry (in-memory; fine for a local single-user app) ───────────
JOBS: dict[str, dict] = {}
JOBS_LOCK = threading.Lock()


def _job_running() -> dict | None:
    with JOBS_LOCK:
        for job in JOBS.values():
            if job["status"] == "running":
                return job
    return None


def _run_job(job_id: str, topic: str, style: str, notes: str, duration: float = 30.0, music: str = "auto"):
    """Background worker: runs the autonomous video factory pipeline with live progress."""
    import argparse
    from scripts.factory import cmd_produce, _slugify

    def prog(frac: float, msg: str):
        with JOBS_LOCK:
            job = JOBS.get(job_id)
            if job:
                job["progress"] = round(frac * 100, 1)
                job["step"] = msg
                # Keep up to 50 logs to prevent memory bloat over long sessions
                if "logs" not in job: job["logs"] = []
                job["logs"].append(msg)
                if len(job["logs"]) > 50:
                    job["logs"].pop(0)

    try:
        prog(0.05, "Initializing Autonomous Factory Engine...")
        prod_id = f"proj_{uuid.uuid4().hex[:8]}"
        topic_slug = _slugify(topic)

        args = argparse.Namespace(
            topic=topic,
            production=prod_id,
            provider="all",
            freshness="7d",
            duration=duration,
        )

        exit_code = cmd_produce(args, progress_cb=prog)
        if exit_code != 0:
            raise RuntimeError(f"Factory production failed with exit code {exit_code}")

        prog(1.0, "Production Complete")
        with JOBS_LOCK:
            job = JOBS.get(job_id)
            if job:
                job.update(status="done", progress=100.0, step="Done",
                           out=topic_slug, finished=datetime.now().isoformat())
    except Exception as exc:
        traceback.print_exc()
        # Clean up any partial output directory since the job failed
        try:
            from pathlib import Path
            import shutil
            out_dir = Path("output")
            if out_dir.exists():
                # Find the most recently created folder that is missing manifest.json
                folders = sorted([d for d in out_dir.iterdir() if d.is_dir()], key=lambda x: x.stat().st_ctime, reverse=True)
                for d in folders:
                    if not (d / "manifest.json").exists():
                        print(f"Cleaning up partial/failed output directory: {d.name}")
                        shutil.rmtree(d, ignore_errors=True)
                        break
        except Exception as cleanup_err:
            print(f"Failed to clean up partial directory: {cleanup_err}")

        with JOBS_LOCK:
            job = JOBS.get(job_id)
            if job:
                job.update(status="error", step="Failed",
                           error=str(exc)[-600:], finished=datetime.now().isoformat())





def provider_statuses():
    return {
        "openai": "key detected" if os.getenv("OPENAI_API_KEY") else "not configured",
        "gemini": "key detected" if os.getenv("GEMINI_API_KEY") else "not configured",
        "openrouter": "key detected" if os.getenv("OPENROUTER_API_KEY") else "not configured",
        "ollama": "host detected" if os.getenv("OLLAMA_HOST") else "not configured",
    }


def _pretty_date(folder_name: str) -> str:
    m = re.search(r"(\d{8})-(\d{6})", folder_name)
    if not m:
        return folder_name
    try:
        dt = datetime.strptime(m.group(1) + m.group(2), "%Y%m%d%H%M%S")
        return dt.strftime("%d %b %H:%M")
    except ValueError:
        return folder_name


def recent_runs():
    runs = []
    if not OUTPUT.exists():
        return runs
    for folder in sorted((p for p in OUTPUT.iterdir() if p.is_dir()),
                         key=lambda p: p.stat().st_mtime, reverse=True)[:8]:
        try:
            m_path = folder / "factory_manifest.json" if (folder / "factory_manifest.json").exists() else (folder / "manifest.json")
            if not m_path.exists():
                continue
            m = json.loads(m_path.read_text(encoding="utf-8"))
            scenes = m.get("scenes", [])
            attempts = m.get("provider_attempts", [])
            last = attempts[-1] if attempts else {"provider": "autonomous-factory", "detail": "Phase 10-17"}
            total_tokens = sum(a.get("tokens", 0) for a in attempts if a.get("status") == "success")
            
            preview_file = "preview.png" if (folder / "preview.png").exists() else ("contact_sheet.png" if (folder / "contact_sheet.png").exists() else "preview.png")
            has_vid = (folder / "final_video.mp4").exists() or (folder / "video.mp4").exists()
            
            runs.append({
                "folder": folder.name,
                "title": m.get("selected_title") or m.get("title", folder.name),
                "source": m.get("source", "autonomous-factory-v2"),
                "style": m.get("style", "claude_editorial"),
                "duration": int(m.get("video_duration_seconds", scenes[-1].get("end_seconds", 0) if scenes else 0)),
                "created": _pretty_date(folder.name),
                "preview": preview_file,
                "has_scenes": (folder / "scenes").exists() or (folder / "factory_manifest.json").exists(),
                "attempt": f"{last.get('provider','factory')}: {last.get('status','ready')}",
                "tokens": total_tokens,
                "video": has_vid,
            })
        except Exception:
            continue
    return runs


def ranked_model_label() -> str:
    try:
        from models import best_label
        return best_label()
    except Exception:
        return "unranked — local template"


from music_catalog import list_music_options


@app.get("/")
def home():
    return render_template('index.html', statuses=provider_statuses(), runs=recent_runs(),
                                  error=None, active_job="",
                                  model_label=ranked_model_label(),
                                  music_options=list_music_options())


@app.post("/create")
def create():
    topic = request.form.get("topic", "").strip()
    style = request.form.get("style", "auto").strip()
    notes = request.form.get("notes", "").strip()
    music = request.form.get("music", "auto").strip()
    dur_raw = request.form.get("duration", "auto").strip().lower()
    if dur_raw == "auto":
        duration = 0.0
    else:
        try:
            duration = float(dur_raw)
        except ValueError:
            duration = 30.0

    if not topic:
        return render_template('index.html', statuses=provider_statuses(), runs=recent_runs(),
                                      error="Enter a topic first.", active_job="",
                                      music_options=list_music_options()), 400

    job_id = uuid.uuid4().hex[:8]
    with JOBS_LOCK:
        JOBS[job_id] = {"id": job_id, "topic": topic, "style": style, "notes": notes, "duration": duration, "music": music,
                        "status": "running", "progress": 0.0, "step": "Starting", "logs": ["Starting pipeline"],
                        "out": "", "error": "", "finished": ""}
    thread = threading.Thread(target=_run_job, args=(job_id, topic, style, notes, duration, music), daemon=True)
    thread.start()
    return redirect(url_for("home"), code=303)


@app.get("/api/job/<job_id>")
def job_status(job_id):
    with JOBS_LOCK:
        job = JOBS.get(job_id)
        if not job:
            abort(404)
        return jsonify(dict(job))


@app.get("/api/jobs")
def all_jobs():
    with JOBS_LOCK:
        return jsonify(dict(JOBS))


@app.post("/api/jobs/clear")
def clear_jobs():
    with JOBS_LOCK:
        JOBS.clear()
    return jsonify({"status": "cleared", "message": "All running instances and queues purged."})


@app.get("/api/status")
def api_status():
    envfile.load_dotenv()  # Re-read .env dynamically
    return jsonify(provider_statuses())


@app.get("/output/<path:filename>")
def output_file(filename):
    path = OUTPUT / filename
    if path.is_dir():
        items = sorted(path.glob("*.png"), key=lambda p: p.name)
        if not items:
            abort(404)
        links = "".join(
            f'<a href="/output/{filename}/{p.name}" style="display:block;padding:8px 0;color:#82d5e8;text-decoration:none;border-bottom:1px solid #1a2e3e">{p.name}</a>'
            for p in items)
        return f'<!doctype html><html><head><meta charset="utf-8"><title>Scenes</title><style>body{{background:#081621;color:#eaf2f7;font:16px system-ui;padding:40px;max-width:600px;margin:auto}}a:hover{{color:#1A5CFF}}</style></head><body><h2>Scene Assets</h2>{links}<p style="margin-top:20px"><a href="/" style="color:#1A5CFF">&larr; Back</a></p></body></html>'
    return send_from_directory(OUTPUT, filename)


if __name__ == "__main__":
    print("Open http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=False, threaded=True)
