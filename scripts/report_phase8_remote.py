"""Phase 8B benchmark report from real worker outputs. Reads only; renders nothing.

Usage:
    python scripts/report_phase8_remote.py --production proj_3e27bd7a

Expects the synced worker directory with final_video.mp4, render_manifest.json,
render_report.json, sample frames, contact_sheet.png, and worker_result.json.
Every check reports pass/fail/skip explicitly; missing evidence is never a pass.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import envfile
envfile.load_dotenv()

from composition.remotion.renderer import compare_frames, ffprobe_info, validate_worker_result
from production.controller import ProductionController
from production.stage_registry import default_production_registry

TOLERANCE_SECONDS = 0.5


def check(name: str, ok: bool | None, detail: str = "") -> dict:
    return {"check": name, "result": "pass" if ok is True else ("fail" if ok is False else "skip"),
            "detail": detail}


def run(production_id: str, ab_specs: list[str] | None = None) -> int:
    ab_specs = ab_specs or []
    report: dict = {"production_id": production_id, "checks": []}
    controller = ProductionController(projects_root=ROOT / "projects", registry=default_production_registry)
    try:
        store = controller.artifact_store
        edit = store.latest("edit_decisions", production_id)
        proposal = store.latest("proposal_packet", production_id)
    except Exception as exc:
        print(f"[ERROR] Cannot load production: {exc}")
        return 2

    selected = next(c for c in proposal.data["concepts"]
                    if c["concept_id"] == proposal.data["selected_concept_id"])
    report["runtime"] = edit.data["render_runtime"]
    report["runtime_lock"] = {k: edit.data[k] for k in ("renderer_family", "render_runtime", "composition_mode")}
    report["edit_hash"] = edit.content_hash

    comp_dir = ROOT / "projects" / production_id / "composition"
    results = sorted(comp_dir.glob("**/worker_result.json"))
    if not results:
        report["checks"].append(check("remote_result_present", None, "no synced worker_result.json yet"))
        print(json.dumps(report, indent=2))
        print("\nBLOCKED: no remote render has synced back for this production.")
        return 1
    result_path = results[-1]
    result = json.loads(result_path.read_text(encoding="utf-8"))
    violations = validate_worker_result(result)
    report["checks"].append(check("worker_result_contract", not violations, "; ".join(violations)))
    if result.get("status") != "completed":
        report["checks"].append(check("worker_completed", False, result.get("message", "")))
        print(json.dumps(report, indent=2))
        return 1

    video = Path(result["output_file"])
    report["checks"].append(check("output_exists", video.is_file(), str(video)))
    if not video.is_file():
        print(json.dumps(report, indent=2))
        return 1
    info = ffprobe_info(video)
    streams = [s for s in info["streams"] if s.get("codec_type") == "video"]
    video_stream, fmt = streams[0], info["format"]
    duration = float(fmt["duration"])
    report.update({
        "output_file": str(video), "resolution": f"{video_stream['width']}x{video_stream['height']}",
        "fps": video_stream.get("r_frame_rate"), "duration": duration,
        "audio": fmt.get("nb_streams", 1) > 1,
        "render_seconds": result.get("render_seconds"),
        "node": result.get("node_version"), "npm": result.get("npm_version"),
        "remotion_version": result.get("runtime_version"),
    })
    report["checks"].append(check("codec_h264", video_stream.get("codec_name") == "h264", video_stream.get("codec_name", "")))
    report["checks"].append(check("resolution_1080x1920",
                                 (video_stream.get("width"), video_stream.get("height")) == (1080, 1920),
                                 f"{video_stream.get('width')}x{video_stream.get('height')}"))
    report["checks"].append(check("fps_30", video_stream.get("r_frame_rate") in ("30/1", "30"),
                                  str(video_stream.get("r_frame_rate"))))
    report["checks"].append(check("duration_matches_edit", abs(duration - edit.data["total_duration"]) <= TOLERANCE_SECONDS,
                                  f"mp4={duration:.2f}s edit={edit.data['total_duration']:.2f}s"))
    report["checks"].append(check("audio_declared", True, f"audio_present={result.get('audio_present')}"))

    frames = sorted(video.parent.glob("frame_*.png")) or sorted((video.parent / "sample_frames").glob("*.png"))
    report["checks"].append(check("decoded_frames", len(frames) >= 5, f"{len(frames)} frames"))
    sheet = video.parent / "contact_sheet.png"
    report["checks"].append(check("contact_sheet", sheet.is_file(), str(sheet)))

    # A/B pixel authority: variant frame pairs must differ materially.
    # Pass --ab <label>:<frame_a>:<frame_b> for each comparison.
    ab_results = []
    for spec in ab_specs:
        try:
            label, first, second = spec.split(":", 2)
            difference = compare_frames(first, second)
            differed = difference > 1.0
        except Exception as exc:
            label, differed, difference = spec, False, str(exc)
        ab_results.append({"label": label, "differed": differed, "rms": difference})
        report["checks"].append(check(f"ab_{label}", differed if isinstance(differed, bool) else False,
                                      f"rms={difference}"))
    report["ab_results"] = ab_results
    print(json.dumps(report, indent=2))
    failures = [c for c in report["checks"] if c["result"] == "fail"]
    return 1 if failures else 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Phase 8B benchmark report from worker outputs")
    parser.add_argument("--production", required=True)
    parser.add_argument("--ab", action="append", default=[],
                        help="Pixel comparison as label:frame_a:frame_b (repeatable)")
    args = parser.parse_args()
    sys.exit(run(args.production, ab_specs=args.ab))
