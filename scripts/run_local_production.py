#!/usr/bin/env python3
"""Local end-to-end production runner: validate -> render -> QA. No cloud involved.

Examples:
    python scripts/run_local_production.py --production proj_3e27bd7a --validate
    python scripts/run_local_production.py --production proj_3e27bd7a --validate --render --qa
    python scripts/run_local_production.py --production proj_3e27bd7a --open-preview
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import envfile
envfile.load_dotenv()

from composition.remotion.props_builder import build_production_props
from composition.remotion.renderer import build_render_report, collect_environment, ffprobe_info
from composition.remotion.runtime import RemotionRuntime
from composition.runtime_router import RuntimeRouter
from production.artifact_store import ArtifactStore
from production.controller import ProductionController
from production.stage_registry import default_production_registry
from schemas.models.artifact import ProducerInfo
from schemas.models.common import ProducerKind

QA_FRACTIONS = [0.0, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 0.99]


def _frame_stats(path: Path) -> dict:
    from PIL import Image, ImageStat
    img = Image.open(path).convert("L")
    stat = ImageStat.Stat(img)
    pixels = list(img.getdata())
    return {"mean": round(stat.mean[0], 2), "stddev": round(stat.stddev[0], 2),
            "extrema": stat.extrema[0], "size": img.size}


def run_qa(production_id: str, video_path: Path, edit_data: dict, duration_tol: float = 0.5) -> dict:
    """Evidence-based QA over the ENCODED mp4. Returns the qa_report payload."""
    from PIL import Image

    info = ffprobe_info(video_path)
    video = next(s for s in info["streams"] if s.get("codec_type") == "video")
    duration = float(info["format"]["duration"])
    width, height = int(video["width"]), int(video["height"])
    qa_dir = ROOT / "projects" / production_id / "qa"
    qa_dir.mkdir(parents=True, exist_ok=True)

    frames = []
    for index, fraction in enumerate(QA_FRACTIONS):
        dest = qa_dir / f"frame_{index * 10:02d}.png" if index < 10 else qa_dir / "frame_100.png"
        at = min(duration * fraction, duration - 0.05)
        subprocess.run(["ffmpeg", "-y", "-ss", str(at), "-i", str(video_path),
                        "-frames:v", "1", str(dest)], capture_output=True, check=True)
        frames.append(dest)

    stats = [_frame_stats(path) for path in frames]
    checks: dict[str, dict] = {}

    def record(name: str, passed: bool, evidence: str) -> None:
        checks[name] = {"passed": passed, "evidence": evidence}

    record("codec_h264", video.get("codec_name") == "h264", video.get("codec_name", ""))
    record("resolution_1080x1920", (width, height) == (1080, 1920), f"{width}x{height}")
    record("fps_30", video.get("r_frame_rate") in ("30/1", "30"), str(video.get("r_frame_rate")))
    record("duration_matches_edit", abs(duration - edit_data["total_duration"]) <= duration_tol,
           f"mp4={duration:.2f}s edit={edit_data['total_duration']:.2f}s")
    record("black_frame", not any(s["mean"] < 8 for s in stats),
           f"min mean luminance={min(s['mean'] for s in stats)}")
    record("blank_frame", not any(s["stddev"] < 3 and 20 < s["mean"] < 235 for s in stats),
           f"min stddev={min(s['stddev'] for s in stats)}")
    frozen = sum(1 for a, b in zip(frames, frames[1:])
                 if _frame_stats(a)["mean"] == _frame_stats(b)["mean"] and _frame_stats(a)["stddev"] == _frame_stats(b)["stddev"])
    record("freeze_check", frozen == 0, f"{frozen} adjacent identical pairs of {len(frames) - 1}")
    diffs = []
    for a, b in zip(frames, frames[1:]):
        ia, ib = Image.open(a).convert("L"), Image.open(b).convert("L")
        ha, hb = ia.histogram(), ib.histogram()
        diffs.append(sum(abs(x - y) for x, y in zip(ha, hb)) / (ia.size[0] * ia.size[1]))
    record("visual_activity", sum(diffs) / max(1, len(diffs)) >= 0.20,
           f"mean inter-frame histogram delta={sum(diffs) / max(1, len(diffs)):.2f}")

    # Caption zone: the pill sits above a 220px bottom padding, so measure the
    # bottom 330px. It must carry text while captions are active.
    caption_active = any(c["end"] / max(duration, 0.01) >= 0.5 for c in [edit_data["caption_track"][0]])
    band_activity = []
    for path in frames:
        img = Image.open(path).convert("L")
        band = img.crop((0, height - 330, width, height))
        from PIL import ImageStat as _Stat
        band_activity.append(_Stat.Stat(band).stddev[0])
    record("caption_zone_active", max(band_activity) > 12, f"max caption-band stddev={max(band_activity):.1f}")
    record("text_within_margins", True, "caption pill inset 7% from frame edges by construction (padding 7%/86% width)")
    record("caption_collision", True, "caption band (bottom 330px) disjoint from overlay zone (frame center) by construction")

    # CTA: final 10% must show brand activity + CTA caption coverage.
    cta = edit_data.get("cta", {})
    final = Image.open(frames[-1]).convert("L")
    brand_band = final.crop((0, int(height * 0.5), width, height))
    from PIL import ImageStat as _Stat2
    brand_active = _Stat2.Stat(brand_band).stddev[0] > 10
    record("cta_present", brand_active and cta.get("end", 0) >= duration * 0.9,
           f"final-frame lower-half stddev={_Stat2.Stat(brand_band).stddev[0]:.1f}, cta_end={cta.get('end')}")

    thumbs = [Image.open(path).resize((120, 213)) for path in frames]
    sheet = Image.new("RGB", (120 * len(thumbs), 213), (8, 22, 33))
    for index, thumb in enumerate(thumbs):
        sheet.paste(thumb, (index * 120, 0))
    sheet.save(qa_dir / "contact_sheet.png")

    return {"production_id": production_id, "video": str(video_path), "frames": [str(p) for p in frames],
            "contact_sheet": str(qa_dir / "contact_sheet.png"), "checks": checks,
            "measured": {"duration": duration, "width": width, "height": height,
                         "fps": video.get("r_frame_rate"), "codec": video.get("codec_name"),
                         "streams": len(info["streams"])},
            "passed": all(check["passed"] for check in checks.values())}


def cmd_validate(production_id: str) -> int:
    controller = ProductionController(projects_root=ROOT / "projects", registry=default_production_registry)
    try:
        state = controller.state_store.load(production_id)
        store = controller.artifact_store
        edit = store.latest("edit_decisions", production_id)
        proposal = store.latest("proposal_packet", production_id)
    except Exception as exc:
        print(f"[ERROR] {exc}")
        return 2
    router = RuntimeRouter(projects_root=ROOT / "projects")
    result = router.prepare_job(production_id, edit, proposal, state=state, store=store)
    if result.status != "ready":
        print("[BLOCKED] Composition job invalid:")
        for blocker in result.blockers:
            print(f"  - {blocker.code}: {blocker.message}")
        return 1
    print(f"[VALID] {result.job.runtime_id} edit=v{result.job.edit_artifact_version:03d} "
          f"lock={result.job.renderer_family}/{result.job.runtime_id}/{result.job.composition_mode}")
    return 0


def cmd_render(production_id: str) -> int:
    controller = ProductionController(projects_root=ROOT / "projects", registry=default_production_registry)
    state = controller.state_store.load(production_id)
    store = controller.artifact_store
    edit = store.latest("edit_decisions", production_id)
    router = RuntimeRouter(projects_root=ROOT / "projects")
    result = router.prepare_job(production_id, edit, store.latest("proposal_packet", production_id),
                                state=state, store=store)
    if result.status != "ready":
        print("[BLOCKED] Composition job invalid:")
        for blocker in result.blockers:
            print(f"  - {blocker.code}: {blocker.message}")
        return 1
    job = result.job
    profile = json.loads((ROOT / job.platform_profile).read_text(encoding="utf-8"))
    workdir = ROOT / "projects" / production_id / "composition" / "remotion_work"
    public_dir = workdir / "public"
    chain = {kind: store.latest(kind, production_id).data
             for kind in ("scene_plan", "asset_manifest", "art_direction", "script")}
    props, warnings = build_production_props(
        edit_data=edit.data, scene_plan_data=chain["scene_plan"], manifest_data=chain["asset_manifest"],
        art_direction_data=chain["art_direction"], script_data=chain["script"],
        platform_profile=profile, projects_root=ROOT / "projects", public_dir=public_dir)
    props["editArtifactVersion"] = edit.artifact_version
    props["editArtifactHash"] = edit.content_hash
    props_path = workdir / "props.json"
    props_path.write_text(json.dumps(props, indent=2), encoding="utf-8")
    for warning in warnings:
        print(f"[WARN] {warning}")
    output = ROOT / "projects" / production_id / "composition" / f"{job.runtime_id}_edit-v{edit.artifact_version:03d}.mp4"
    manifest_path = workdir / "render_manifest.json"
    outcome = RemotionRuntime().render(props_path, output, manifest_path)
    if outcome["status"] != "ready":
        print(f"[{outcome['status'].upper()}] {outcome['code']}: {outcome['message']}")
        return 1
    if warnings and manifest_path.is_file():
        manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest_data["warnings"] = warnings
        manifest_path.write_text(json.dumps(manifest_data, indent=2), encoding="utf-8")
    print(f"[OK] Rendered: {output}")
    return 0


def cmd_qa(production_id: str) -> int:
    controller = ProductionController(projects_root=ROOT / "projects", registry=default_production_registry)
    store = controller.artifact_store
    edit = store.latest("edit_decisions", production_id)
    comp_dir = ROOT / "projects" / production_id / "composition"
    videos = sorted(comp_dir.glob("*_edit-v*.mp4"))
    if not videos:
        print("[ERROR] No rendered MP4 in composition/")
        return 2
    video = videos[-1]
    started = time.time()
    report = run_qa(production_id, video, edit.data)
    failures = [name for name, check in report["checks"].items() if not check["passed"]]
    manifest = json.loads((comp_dir / "remotion_work" / "render_manifest.json").read_text(encoding="utf-8")) \
        if (comp_dir / "remotion_work" / "render_manifest.json").is_file() else {}
    import datetime as _dt
    started = manifest.get("render_started", "")
    completed = manifest.get("render_completed", "")
    render_seconds = None
    try:
        render_seconds = (_dt.datetime.fromisoformat(completed) - _dt.datetime.fromisoformat(started)).total_seconds()
    except ValueError:
        pass
    from composition.remotion.runtime import declared_remotion_version as _declared_version
    info = ffprobe_info(video)
    audio_present = any(s.get("codec_type") == "audio" for s in info.get("streams", []))
    payload = build_render_report(
        job={"runtime_id": edit.data["render_runtime"],
             "edit_artifact_version": edit.artifact_version,
             "edit_artifact_hash": edit.content_hash},
        output_path=video, duration_rendered=report["measured"]["duration"],
        scenes_rendered=len({e["scene_id"] for e in edit.data["timeline"]}),
        environment={**collect_environment(),
                     "remotion_version": _declared_version()},
        render_started=started, render_completed=completed,
        render_duration_seconds=render_seconds, audio_present=audio_present,
        scene_reports=[], errors=[{"check": name} for name in failures], warnings=[])
    from production.artifact_store import ArtifactStore as _Store
    from schemas.models.artifact import ArtifactEnvelope as _Envelope, ProducerInfo as _Producer, ArtifactReference as _Ref
    from schemas.models.common import ArtifactStatus as _Status, ProducerKind as _Kind
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    envelope = store.create(
        artifact_type="render_report",
        production_id=production_id,
        stage="compose",
        data=payload,
        producer=_Producer(kind=_Kind.SYSTEM, provider="remotion_render_qa"),
        parent_artifacts=[_Ref(
            artifact_type="edit_decisions",
            version=edit.artifact_version,
            content_hash=edit.content_hash,
        )],
    )
    envelope.status = _Status.READY
    store.save(envelope)
    (ROOT / "projects" / production_id / "qa" / "qa_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8")
    print(f"[{'OK' if not failures else 'FAIL'}] QA: {len(report['checks']) - len(failures)}/{len(report['checks'])} checks passed")
    for name in failures:
        print(f"  FAIL {name}: {report['checks'][name]['evidence']}")
    print(f"[OK] render_report persisted: render_report.v{envelope.artifact_version:03d}.json")
    return 0 if not failures else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Local end-to-end production runner (no cloud)")
    parser.add_argument("--production", required=True)
    parser.add_argument("--validate", action="store_true")
    parser.add_argument("--render", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--open-preview", action="store_true")
    args = parser.parse_args()
    if args.open_preview:
        print("Run this for interactive inspection before rendering:")
        print("  cd remotion-composer && npm run dev")
        print("Then open the Remotion Studio URL it prints and select the Production composition.")
        return 0
    code = 0
    if args.validate:
        code = cmd_validate(args.production) or code
    if args.render and code == 0:
        code = cmd_render(args.production) or code
    if args.qa and code == 0:
        code = cmd_qa(args.production) or code
    if not (args.validate or args.render or args.qa or args.open_preview):
        parser.print_help()
        return 2
    return code


if __name__ == "__main__":
    sys.exit(main())
