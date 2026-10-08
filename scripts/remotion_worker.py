#!/usr/bin/env python3
"""Remote Remotion worker. Executes a CompositionJob bundle, nothing else.

Usage (Colab or any Node-capable worker):
    python scripts/remotion_worker.py --bundle <job.zip> --workdir <dir> --sync-dir <results dir>
    python scripts/remotion_worker.py --bundle <job.zip> --dry-run   # validate only, no npm/render

Steps: receive, validate job, materialize, verify hashes/artifacts/assets/
project, install pinned deps, tsc validate, render, ffprobe, frames, contact
sheet, render report, worker_result.json, sync. Any failure returns an
explicit failed result. No fallback to any other runtime, ever.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

NODE_MAJOR_REQUIRED = 20
COMMAND_TIMEOUT = 3600

REQUIRED_PROPS_FILES = (
    "props.json", "edit_decisions.json", "scene_plan.json", "asset_manifest.json",
    "art_direction.json", "script.json",
)
REQUIRED_COMPOSER_FILES = (
    "package.json", "tsconfig.json", "remotion.config.ts",
    "src/index.ts", "src/Root.tsx",
    "src/compositions/ProductionComposition.tsx",
    "src/compositions/SceneComposition.tsx",
)


def log(message: str, logs: list) -> None:
    line = f"[worker] {message}"
    print(line, flush=True)
    logs.append(line)


def fail(job_id: str, code: str, message: str, logs: list, sync_dir: Path | None,
         extra: dict | None = None) -> int:
    result = {"status": "failed", "job_id": job_id, "runtime": "remotion",
              "code": code, "message": message, "logs": logs[-40:]}
    if extra:
        result.update(extra)
    print(json.dumps(result, indent=2))
    if sync_dir is not None:
        sync_dir.mkdir(parents=True, exist_ok=True)
        (sync_dir / "worker_result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return 1


def canonical_hash(data: dict) -> str:
    canonical = json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def run_command(argv: list[str], cwd: Path, logs: list) -> subprocess.CompletedProcess:
    log(f"$ {' '.join(argv)}", logs)
    try:
        return subprocess.run(argv, cwd=cwd, capture_output=True, text=True, timeout=COMMAND_TIMEOUT)
    except (OSError, subprocess.SubprocessError) as exc:
        raise RuntimeError(f"command failed to start: {exc}") from exc


def main() -> int:
    parser = argparse.ArgumentParser(description="Remote Remotion composition worker")
    parser.add_argument("--bundle", required=True, help="remote-job bundle zip")
    parser.add_argument("--workdir", default=None, help="working directory (default: temp)")
    parser.add_argument("--sync-dir", default=None, help="results directory (Drive folder on Colab)")
    parser.add_argument("--dry-run", action="store_true", help="validate only; skip npm install and render")
    parser.add_argument("--install-node", action="store_true", help="apt-install Node 20 if missing (linux worker)")
    args = parser.parse_args()

    logs: list = []
    sync_dir = Path(args.sync_dir) if args.sync_dir else None
    bundle = Path(args.bundle)
    if not bundle.is_file():
        return fail("unknown", "BUNDLE_MISSING", f"Bundle not found: {bundle}", logs, sync_dir)

    workdir = Path(args.workdir) if args.workdir else Path(tempfile.mkdtemp(prefix="remotion_work_"))
    workdir.mkdir(parents=True, exist_ok=True)

    # 1-2. Receive + validate job.
    try:
        with zipfile.ZipFile(bundle) as archive:
            archive.extractall(workdir)
    except Exception as exc:
        return fail("unknown", "BUNDLE_CORRUPT", f"Cannot unpack bundle: {exc}", logs, sync_dir)
    remote_job_path = workdir / "remote_job.json"
    if not remote_job_path.is_file():
        return fail("unknown", "JOB_MISSING", "Bundle has no remote_job.json", logs, sync_dir)
    job = json.loads(remote_job_path.read_text(encoding="utf-8"))
    job_id = str(job.get("production_id", "unknown"))
    if job.get("runtime") != "remotion":
        return fail(job_id, "RUNTIME_LOCK_MISMATCH",
                    f"Worker executes remotion only; job locks {job.get('runtime')!r}.", logs, sync_dir)
    for key in ("production_id", "edit_artifact_version", "edit_artifact_hash", "platform_profile"):
        if key not in job:
            return fail(job_id, "JOB_INVALID", f"Job missing required key: {key}", logs, sync_dir)
    log(f"job accepted: {job_id} edit=v{job['edit_artifact_version']:03d}", logs)

    props_dir = workdir / "props"
    assets_dir = workdir / "assets"
    composer_dir = workdir / "composer"

    # 3-7. Materialize + verify (hash, artifacts, assets, project).
    for name in REQUIRED_PROPS_FILES:
        if not (props_dir / name).is_file():
            return fail(job_id, "PROPS_MISSING", f"Bundle missing props/{name}", logs, sync_dir)
    props = json.loads((props_dir / "props.json").read_text(encoding="utf-8"))
    edit = json.loads((props_dir / "edit_decisions.json").read_text(encoding="utf-8"))
    if canonical_hash(edit) != job["edit_artifact_hash"]:
        return fail(job_id, "EDIT_HASH_MISMATCH",
                    "edit_decisions.json hash does not match the job's locked edit hash.", logs, sync_dir)
    log("edit hash verified against job lock", logs)
    for asset_file in sorted(assets_dir.glob("*")):
        if asset_file.stat().st_size == 0:
            return fail(job_id, "ASSET_MISSING", f"Asset file empty: {asset_file.name}", logs, sync_dir)
    for asset in props.get("assets", []):
        if asset.get("publicPath") and not (composer_dir / "public" / asset["publicPath"]).is_file() \
                and not (assets_dir / Path(asset["publicPath"]).name).is_file():
            return fail(job_id, "ASSET_MISSING",
                        f"Props reference asset with no bundled file: {asset.get('asset_id')}", logs, sync_dir)
    log(f"assets verified: {len(props.get('assets', []))} declared", logs)
    for name in REQUIRED_COMPOSER_FILES:
        if not (composer_dir / name).is_file():
            return fail(job_id, "COMPOSER_INCOMPLETE", f"Composer project missing: {name}", logs, sync_dir)
    pinned = json.loads((composer_dir / "package.json").read_text(encoding="utf-8")).get("dependencies", {}).get("remotion")
    log(f"composer project verified (pinned remotion {pinned})", logs)

    if args.dry_run:
        log("dry-run: validation complete, skipping npm install and render", logs)
        result = {"status": "completed", "job_id": job_id, "runtime": "remotion",
                  "dry_run": True, "exit_code": 0,
                  "output_file": None, "logs": logs[-40:]}
        print(json.dumps(result, indent=2))
        if sync_dir is not None:
            sync_dir.mkdir(parents=True, exist_ok=True)
            (sync_dir / "worker_result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        return 0

    # 8. Pinned dependencies (npm ci when locked, else install + record tree).
    node = shutil.which("node")
    if node is None and args.install_node and sys.platform.startswith("linux"):
        log("installing Node 20 via nodesource", logs)
        setup = run_command(["bash", "-lc",
                             "curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash - && sudo apt-get install -y nodejs"],
                            workdir, logs)
        if setup.returncode != 0:
            return fail(job_id, "NODE_INSTALL_FAILED", (setup.stderr or "")[-800:], logs, sync_dir)
        node = shutil.which("node")
    if node is None:
        return fail(job_id, "NODE_MISSING", "node executable not found and --install-node not given", logs, sync_dir)
    lockfile = composer_dir / "package-lock.json"
    install = run_command(["npm", "ci" if lockfile.is_file() else "install", "--no-audit", "--no-fund"],
                          composer_dir, logs)
    if install.returncode != 0:
        return fail(job_id, "NPM_INSTALL_FAILED", (install.stderr or "")[-800:], logs, sync_dir)
    tree = run_command(["npm", "ls", "--json"], composer_dir, logs)
    resolved = {}
    try:
        resolved = json.loads(tree.stdout or "{}").get("dependencies", {})
    except ValueError:
        pass
    log(f"dependencies installed (remotion@{resolved.get('remotion', {}).get('version', '?')})", logs)

    # 9. TypeScript + composition validation.
    validate = run_command(["npm", "run", "validate"], composer_dir, logs)
    if validate.returncode != 0:
        return fail(job_id, "TSC_VALIDATION_FAILED", (validate.stdout or "")[-800:] + (validate.stderr or "")[-800:],
                    logs, sync_dir)

    # 10. Render via the project's documented command.
    public_assets = composer_dir / "public" / "assets"
    public_assets.mkdir(parents=True, exist_ok=True)
    for asset_file in sorted(assets_dir.glob("*")):
        shutil.copyfile(asset_file, public_assets / asset_file.name)
    output = workdir / "final_video.mp4"
    manifest_path = workdir / "render_manifest.json"
    render_cmd = ["node", "scripts/render.mjs", "--props", str(props_dir / "props.json"),
                  "--output", str(output), "--manifest", str(manifest_path)]
    import time as _time
    started, wall_start = _datetime_now(), _time.time()
    rendered = run_command(render_cmd, composer_dir, logs)
    render_seconds = round(_time.time() - wall_start, 1)
    if rendered.returncode != 0 or not output.is_file():
        return fail(job_id, "REMOTION_RENDER_FAILED",
                    ((rendered.stderr or "") + (rendered.stdout or ""))[-1200:] or "no output produced",
                    logs, sync_dir)
    completed = _datetime_now()
    log(f"rendered {output} in {render_seconds}s", logs)

    # 11-13. ffprobe, frames, contact sheet.
    try:
        from PIL import Image
    except ImportError:
        return fail(job_id, "WORKER_ENV_INCOMPLETE", "Pillow required on worker for QA frames", logs, sync_dir)
    probe = run_command(["ffprobe", "-v", "quiet", "-print_format", "json",
                         "-show_format", "-show_streams", str(output)], workdir, logs)
    if probe.returncode != 0:
        return fail(job_id, "FFPROBE_FAILED", (probe.stderr or "")[-500:], logs, sync_dir)
    streams = [s for s in json.loads(probe.stdout)["streams"] if s.get("codec_type") == "video"]
    video = streams[0]
    duration = float(json.loads(probe.stdout)["format"]["duration"])
    frames_dir = workdir / "sample_frames"
    frames_dir.mkdir(exist_ok=True)
    fractions = {"frame_00": 0.01, "frame_25": 0.25, "frame_50": 0.50, "frame_75": 0.75, "frame_100": 0.99}
    for name, fraction in fractions.items():
        at = run_command(["ffmpeg", "-y", "-ss", str(duration * fraction), "-i", str(output),
                          "-frames:v", "1", str(frames_dir / f"{name}.png")], workdir, logs)
        if at.returncode != 0:
            return fail(job_id, "FRAME_EXTRACTION_FAILED", (at.stderr or "")[-500:], logs, sync_dir)
    thumbs = [Image.open(frames_dir / f"{name}.png").resize((180, 320)) for name in fractions]
    sheet = Image.new("RGB", (180 * len(thumbs), 320), (8, 22, 33))
    for index, thumb in enumerate(thumbs):
        sheet.paste(thumb, (index * 180, 0))
    sheet.save(workdir / "contact_sheet.png")

    # 14-15. Render report + worker result.
    environment = {
        "os": sys.platform,
        "node_version": _version_of(["node", "--version"]),
        "npm_version": _version_of(["npm", "--version"]),
        "remotion_version": resolved.get("remotion", {}).get("version"),
        "ffmpeg_version": _first_line(["ffprobe", "-version"]),
    }
    report = {
        "final_video_path": str(output),
        "duration_rendered": duration,
        "scenes_rendered": len({e.get("scene_id") for e in props.get("events", [])}),
        "render_runtime_used": "remotion",
        "codec": video.get("codec_name"),
        "resolution": f"{video.get('width')}x{video.get('height')}",
        "fps": video.get("r_frame_rate"),
        "file_size_bytes": output.stat().st_size,
        "render_duration_seconds": render_seconds,
        "audio_present": False,
        "cta_present": True,
        "scene_reports": [],
        "errors": [],
        "warnings": [],
        "environment": environment,
        "edit_artifact_version": job["edit_artifact_version"],
        "edit_artifact_hash": job["edit_artifact_hash"],
        "render_started": started,
        "render_completed": completed,
    }
    (workdir / "render_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    result = {
        "status": "completed", "job_id": job_id, "runtime": "remotion",
        "runtime_version": environment["remotion_version"],
        "output_file": str(output), "duration": duration,
        "resolution": report["resolution"], "fps": report["fps"],
        "audio_present": False, "exit_code": 0, "render_seconds": render_seconds,
    }
    (workdir / "worker_result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")

    # 16. Sync results.
    if sync_dir is not None:
        sync_dir.mkdir(parents=True, exist_ok=True)
        for name in ("final_video.mp4", "render_manifest.json", "render_report.json",
                     "contact_sheet.png", "worker_result.json"):
            shutil.copyfile(workdir / name, sync_dir / name)
        out_frames = sync_dir / "sample_frames"
        out_frames.mkdir(exist_ok=True)
        for frame in sorted(frames_dir.glob("*.png")):
            shutil.copyfile(frame, out_frames / frame.name)
        log(f"results synced to {sync_dir}", logs)
    print(json.dumps(result, indent=2))
    return 0


def _datetime_now() -> str:
    import datetime
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _version_of(argv: list[str]) -> str | None:
    try:
        proc = subprocess.run(argv, capture_output=True, text=True, timeout=30)
        if proc.returncode != 0:
            return None
        lines = (proc.stdout or proc.stderr or "").strip().splitlines()
        return lines[0][:120] if lines else None
    except (OSError, subprocess.SubprocessError):
        return None


def _first_line(argv: list[str]) -> str | None:
    return _version_of(argv)


if __name__ == "__main__":
    sys.exit(main())
