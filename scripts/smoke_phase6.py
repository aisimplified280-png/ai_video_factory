"""Real Phase 6 smoke benchmark: pipeline inputs through canonical edit decisions.

Default path runs Phase 1–6 for the specified topic. Use --reuse-production to run
the edit stage against an existing real Phase 5 manifest without regenerating assets.
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

from production.controller import ProductionController
from production.stage_registry import default_production_registry
from schemas.models.common import RunMode
from scripts.smoke_phase5 import DEFAULT_TOPIC_SOURCES


def print_report(edit: dict, manifest: dict, project_dir: Path, directory: Path, version: int) -> None:
    rhythm, utility, cta = edit["rhythm"], edit["asset_utilization_report"], edit["cta"]
    platform = edit.get("platform", {})
    resolution = platform.get("resolution", {})
    manifest_assets = {asset["asset_id"]: asset for asset in manifest.get("assets", [])}
    primary = [event for event in edit["timeline"] if event.get("role") == "primary_visual"]
    missing_manifest = sorted({event["asset_id"] for event in primary if event.get("asset_id") not in manifest_assets})
    missing_files = []
    for event in primary:
        asset = manifest_assets.get(event.get("asset_id"), {})
        path = asset.get("file_path")
        if path and not asset.get("diagram_spec") and asset.get("source") != "native":
            candidate = ROOT / Path(str(path).replace("\\", "/"))
            if not candidate.exists():
                missing_files.append(f"{event['event_id']} -> {path}")
    print("\n" + "=" * 68)
    print(" PHASE 6: EDIT DECISION SMOKE BENCHMARK")
    print("=" * 68)
    print(f"Scenes:                 {len({e['scene_id'] for e in edit['timeline']})}")
    print(f"Shots:                  {rhythm['shot_count']}")
    print(f"Average shot duration:  {rhythm['average_shot_duration']}s")
    print(f"Average cut interval:   {rhythm['average_cut_interval']}s")
    print(f"Transition diversity:   {rhythm['transition_diversity']} {rhythm['transition_counts']}")
    print(f"Video layer count:      {len(edit['video_tracks'])} {sorted(edit['video_tracks'])}")
    print(f"Assets used / unused:   {len(utility['used_assets'])} / {len(utility['unused_assets'])}")
    print(f"CTA timing:             {cta['start']:.2f}s to {cta['end']:.2f}s")
    print(f"Timeline coverage:      {edit['validation']['duration_covered']}")
    print(f"Narration coverage:     {edit['validation']['audio_valid']}")
    print(f"Visual change count:    {rhythm['shot_count']}")
    print(f"Platform lock:          {resolution.get('width')}x{resolution.get('height')} at {platform.get('fps')}fps")
    print(f"SFX reservations:       {len(edit['audio_tracks']['sfx'])}")
    print("\nTimeline proof:")
    print(f"  Primary shots resolved to manifest assets: {len(primary) - len(missing_manifest)}/{len(primary)}")
    print(f"  Manifest assets missing from timeline:      {missing_manifest or 'none'}")
    print(f"  Timeline files missing from disk:           {missing_files or 'none'}")
    print("\nShot sequence:")
    for event in primary:
        asset = manifest_assets.get(event.get("asset_id"), {})
        print(f"  {event['start']:5.2f}-{event['end']:5.2f}s {event['scene_id']} {event.get('shot_id')}: {asset.get('type')}/{asset.get('source')} for '{event['purpose']}' [{event.get('transition_in')}]")
    print("\nArtifacts:")
    for name in (f"edit_decisions.v{version:03d}.json", "edit_review_report.json", "asset_utilization_report.json", "edit_generation_report.json", "edit_summary.md"):
        print(f"  {directory / name}")


def run(topic: str, pipeline: str, reuse_production: str | None = None) -> None:
    controller = ProductionController(projects_root=ROOT / "projects", registry=default_production_registry)
    if reuse_production:
        pid = reuse_production
    else:
        options = {"research_depth": "standard", "run_mode": RunMode.AUTO.value}
        if topic in DEFAULT_TOPIC_SOURCES:
            options["source_urls"] = DEFAULT_TOPIC_SOURCES[topic]
        state = controller.start(topic=topic, pipeline=pipeline, options=options)
        pid = state.project_id
        for stage in ("research", "proposal", "art_direction", "script", "scene_plan", "assets"):
            result = controller.run_stage(pid, stage, options=options)
            if result.status.value == "waiting_approval":
                controller.approve(pid, stage)
            elif result.status.value != "ready":
                raise RuntimeError(f"{stage} failed: {result.message}")
    result = controller.run_stage(pid, "edit")
    if result.status.value != "ready":
        raise RuntimeError(f"edit failed: {result.message}")
    edit_artifact = controller.artifact_store.latest("edit_decisions", pid)
    manifest_artifact = controller.artifact_store.latest("asset_manifest", pid)
    print_report(edit_artifact.data, manifest_artifact.data, ROOT / "projects" / pid, ROOT / "projects" / pid / "edit", edit_artifact.artifact_version)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Phase 6 real edit-plan smoke benchmark")
    parser.add_argument("--topic", default="How OpenAI Built An Empire")
    parser.add_argument("--pipeline", default="youtube-short")
    parser.add_argument("--reuse-production", help="Existing Phase 5 production ID; avoids regenerating upstream artifacts.")
    args = parser.parse_args()
    run(args.topic, args.pipeline, args.reuse_production)
