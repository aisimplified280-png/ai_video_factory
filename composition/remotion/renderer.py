"""Render-side helpers: manifests, reports, remote bundles, frame comparison.

Pure functions over execution records. Nothing here renders; the worker calls
these after a real render, and unit tests call them with fixture logs.
"""
from __future__ import annotations

import datetime as _datetime
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from PIL import Image, ImageChops


def _utcnow() -> str:
    return _datetime.datetime.now(_datetime.timezone.utc).isoformat()


def build_render_manifest(execution_log: dict[str, Any]) -> dict[str, Any]:
    """Describe what actually executed, from a worker execution log."""
    return {
        "production_id": execution_log.get("production_id"),
        "edit_artifact_version": execution_log.get("edit_artifact_version"),
        "edit_artifact_hash": execution_log.get("edit_artifact_hash"),
        "runtime": execution_log.get("runtime", "remotion"),
        "runtime_version": execution_log.get("runtime_version"),
        "renderer_family": execution_log.get("renderer_family"),
        "composition_mode": execution_log.get("composition_mode"),
        "profile": execution_log.get("profile"),
        "scenes": execution_log.get("scenes", []),
        "shots_executed": execution_log.get("shots_executed", []),
        "assets_executed": execution_log.get("assets_executed", []),
        "motions_executed": execution_log.get("motions_executed", []),
        "camera_operations": execution_log.get("camera_operations", []),
        "transitions_executed": execution_log.get("transitions_executed", []),
        "captions_executed": execution_log.get("captions_executed", []),
        "audio_tracks": execution_log.get("audio_tracks", []),
        "cta_executed": execution_log.get("cta_executed", False),
        "warnings": execution_log.get("warnings", []),
        "errors": execution_log.get("errors", []),
    }


def build_render_report(
    *,
    job: Any,
    output_path: Path | str,
    duration_rendered: float,
    scenes_rendered: int,
    environment: dict[str, Any],
    render_started: str,
    render_completed: str,
    render_duration_seconds: float | None = None,
    scene_reports: list[dict] | None = None,
    errors: list | None = None,
    warnings: list | None = None,
    audio_present: bool = False,
    parent_artifacts: list[dict] | None = None,
) -> dict[str, Any]:
    """Build the canonical render_report payload (validated by tests, persisted by workers)."""
    output_path = Path(output_path)
    get = (lambda key: job.get(key)) if isinstance(job, dict) else (lambda key: getattr(job, key))
    return {
        "final_video_path": output_path.as_posix(),
        "duration_rendered": duration_rendered,
        "scenes_rendered": scenes_rendered,
        "render_runtime_used": get("runtime_id"),
        "codec": "h264",
        "resolution": "1080x1920",
        "fps": 30,
        "file_size_bytes": output_path.stat().st_size if output_path.is_file() else None,
        "render_duration_seconds": render_duration_seconds,
        "scene_reports": scene_reports or [],
        "errors": errors or [],
        "warnings": warnings or [],
        "audio_present": audio_present,
        "environment": environment,
        "edit_artifact_version": get("edit_artifact_version"),
        "edit_artifact_hash": get("edit_artifact_hash"),
        "render_started": render_started,
        "render_completed": render_completed,
    }


REMOTE_BUNDLE_VERSION = "remote-job/v1"

WORKER_RESULT_SCHEMA = {
    "completed": {"required": ["status", "job_id", "runtime", "output_file", "exit_code"],
                  "status_value": "completed"},
    "failed": {"required": ["status", "code", "message"],
               "status_value": "failed"},
}


def collect_environment(node_bin: str | None = None) -> dict[str, Any]:
    """Record the executing environment for the render report. Read-only probes."""
    import platform as _platform
    import shutil as _shutil

    def _version(binary: str | None, args: list[str]) -> str | None:
        if not binary:
            return None
        try:
            proc = subprocess.run([binary, *args], capture_output=True, text=True, timeout=30)
            if proc.returncode != 0:
                return None
            out = (proc.stdout or proc.stderr or "").strip().splitlines()
            return out[0][:120] if out else None
        except (OSError, subprocess.SubprocessError):
            return None

    node = node_bin or _shutil.which("node")
    npm = _shutil.which("npm")
    return {
        "os": f"{_platform.system()} {_platform.release()}",
        "node_version": _version(node, ["--version"]),
        "npm_version": _version(npm, ["--version"]),
        "ffmpeg_version": _version(_shutil.which("ffmpeg"), ["-version"]),
    }


def validate_worker_result(result: dict[str, Any]) -> list[str]:
    """Check a worker_result.json against the remote result contract.

    Returns a list of violations (empty means valid). Never executes anything.
    """
    violations = []
    if not isinstance(result, dict):
        return ["worker result is not a JSON object"]
    status = result.get("status")
    if status == "completed":
        for key in WORKER_RESULT_SCHEMA["completed"]["required"]:
            if key not in result:
                violations.append(f"completed result missing required key: {key}")
        if result.get("runtime") != "remotion":
            violations.append(f"completed result has wrong runtime: {result.get('runtime')!r}")
        if result.get("exit_code") != 0:
            violations.append(f"completed result has nonzero exit_code: {result.get('exit_code')}")
    elif status == "failed":
        for key in WORKER_RESULT_SCHEMA["failed"]["required"]:
            if key not in result:
                violations.append(f"failed result missing required key: {key}")
    else:
        violations.append(f"unknown worker result status: {status!r} (expected completed|failed)")
    return violations


def package_remote_bundle(
    *,
    job: Any,
    props_path: Path | str,
    artifact_payloads: dict[str, Any],
    asset_files: list[Path | str],
    bundle_path: Path | str,
    composer_dir: Path | str,
    include_composer: bool = False,
) -> Path:
    """Package everything a remote worker needs: job, props, artifacts, assets.

    With include_composer=True the remotion-composer source tree (minus
    node_modules/.git) is embedded so the worker needs no repository access.
    Returns the bundle path. The bundle never contains rendered output.
    """
    get = (lambda key: job.get(key)) if isinstance(job, dict) else (lambda key: getattr(job, key))
    bundle_path = Path(bundle_path)
    staging = bundle_path.parent / (bundle_path.stem + "_staging")
    if staging.exists():
        shutil.rmtree(staging)
    (staging / "props").mkdir(parents=True)
    (staging / "assets").mkdir(parents=True)
    shutil.copyfile(props_path, staging / "props" / "props.json")
    for name, payload in artifact_payloads.items():
        (staging / "props" / f"{name}.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    for asset in asset_files:
        shutil.copyfile(asset, staging / "assets" / Path(asset).name)
    if include_composer:
        shutil.copytree(
            composer_dir, staging / "composer",
            ignore=shutil.ignore_patterns("node_modules", ".git", "__pycache__", "*.pyc"),
        )
    remote_job = {
        "bundle_version": REMOTE_BUNDLE_VERSION,
        "runtime": "remotion",
        "production_id": get("production_id"),
        "edit_artifact_version": get("edit_artifact_version"),
        "edit_artifact_hash": get("edit_artifact_hash"),
        "renderer_family": get("renderer_family"),
        "composition_mode": get("composition_mode"),
        "platform_profile": get("platform_profile"),
        "output_format": get("output_format"),
        "remote_policy": get("remote_policy"),
        "composer_dir": str(composer_dir),
        "worker_steps": ["npm install", "validate props", "remotion render", "write render_manifest.json", "sync back mp4 + reports"],
    }
    (staging / "remote_job.json").write_text(json.dumps(remote_job, indent=2), encoding="utf-8")
    archive = shutil.make_archive(str(bundle_path.parent / bundle_path.stem), "zip", staging)
    shutil.rmtree(staging)
    return Path(archive)


def ffprobe_info(video_path: Path | str) -> dict[str, Any]:
    """Probe an encoded MP4. Raises on failure; used post-render only."""
    proc = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", str(video_path)],
        capture_output=True, text=True, timeout=120,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"ffprobe failed for {video_path}: {(proc.stderr or '').strip()[-500:]}")
    return json.loads(proc.stdout)


def compare_frames(first: Path | str, second: Path | str) -> float:
    """Root-mean-square pixel difference between two frames (0.0 = identical)."""
    left = Image.open(first).convert("RGB")
    right = Image.open(second).convert("RGB")
    if left.size != right.size:
        right = right.resize(left.size)
    diff = ImageChops.difference(left, right)
    histogram = diff.histogram()
    squares = sum(count * ((index % 256) ** 2) for index, count in enumerate(histogram))
    pixels = left.size[0] * left.size[1] * 3
    return (squares / pixels) ** 0.5


def frames_differ(first: Path | str, second: Path | str, threshold: float = 1.0) -> bool:
    """True when two frames differ beyond an encoding-noise threshold."""
    return compare_frames(first, second) > threshold
