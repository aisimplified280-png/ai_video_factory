"""Audit Phase 6 contract integrity for a real production (read-only, no rendering).

Verifies that edit_decisions inherits the approved proposal runtime lock,
that parent lineage is exact, that fallback assets resolve, that asset paths
do not depend on the working directory, and that CTA/rhythm checks hold.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import envfile
envfile.load_dotenv()

from production.controller import ProductionController
from production.dependencies import find_stale_artifacts
from production.stage_registry import default_production_registry
from stages.edit.edit_validator import EditValidator
from stages.edit.timeline import resolve_asset_path

REQUIRED_PARENTS = ("research_brief", "proposal_packet", "art_direction", "script", "scene_plan", "asset_manifest")
BANNED_IMPLEMENTATION_TOKENS = ("from PIL", "ImageDraw", "Image.new", "React", "useState", "className", "<div", "StyleSheet")
_STOPWORDS = {"a", "an", "and", "as", "at", "by", "for", "from", "in", "into", "of", "on", "or", "the", "to", "with"}


def _tokens(value: object) -> set[str]:
    words = str(value or "").lower().replace("-", " ").split()
    return {word.strip(".,;:!?()[]\"'") for word in words} - _STOPWORDS - {""}


def load_production(production_id: str):
    controller = ProductionController(projects_root=ROOT / "projects", registry=default_production_registry)
    state = controller.state_store.load(production_id)
    store = controller.artifact_store
    inputs = {kind: store.latest(kind, production_id) for kind in REQUIRED_PARENTS}
    edit = store.latest("edit_decisions", production_id)
    return controller, state, store, inputs, edit


def audit(production_id: str) -> dict:
    controller, state, store, inputs, edit = load_production(production_id)
    proposal = inputs["proposal_packet"].data
    selected = next(c for c in proposal["concepts"] if c["concept_id"] == proposal["selected_concept_id"])
    proposal_lock = {k: selected[k] for k in ("renderer_family", "render_runtime", "composition_mode")}
    edit_lock = {k: edit.data[k] for k in proposal_lock}
    runtime_match = proposal_lock == edit_lock

    lineage = EditValidator.validate_artifact_lineage(edit, inputs)
    stale = find_stale_artifacts(state, store)

    manifest = inputs["asset_manifest"].data
    scene_plan = inputs["scene_plan"].data
    scenes = {s.get("scene_id") or s.get("id"): s for s in scene_plan.get("scenes", [])}
    manifest_assets = {a.get("asset_id"): a for a in manifest.get("assets", [])}
    primary_events = [e for e in edit.data.get("timeline", []) if e.get("role") == "primary_visual"]
    missing_manifest = sorted({e.get("asset_id") for e in primary_events if e.get("asset_id") not in manifest_assets})

    generation_path = ROOT / "projects" / production_id / "assets" / "asset_generation_report.json"
    generation = json.loads(generation_path.read_text(encoding="utf-8")) if generation_path.exists() else {}
    fallbacks = []
    for attempt in generation.get("generation_attempts", []):
        if attempt.get("action") != "fallback_applied":
            continue
        asset = manifest_assets.get(attempt.get("asset_id"), {})
        scene = scenes.get(asset.get("scene_id"), {})
        resolved = resolve_asset_path(production_id, asset, ROOT / "projects")
        exists = asset.get("source") == "native" or bool(asset.get("diagram_spec")) or (resolved is not None and resolved.exists())
        preserved = bool(_tokens(asset.get("purpose")) & _tokens(scene.get("visual_purpose")))
        fallbacks.append({
            "asset_id": attempt.get("asset_id"),
            "original_strategy": attempt.get("original_strategy"),
            "fallback_strategy": asset.get("fallback_used"),
            "reason": attempt.get("reason"),
            "purpose": asset.get("purpose"),
            "file_exists_or_native": exists,
            "semantic_purpose_preserved": preserved,
            "valid": exists and preserved,
        })

    file_assets = [a for a in manifest_assets.values() if a.get("file_path")]
    first_paths = [resolve_asset_path(production_id, a, ROOT / "projects") for a in file_assets]
    previous_cwd = Path.cwd()
    try:
        os.chdir(tempfile.gettempdir())
        second_paths = [resolve_asset_path(production_id, a, ROOT / "projects") for a in file_assets]
    finally:
        os.chdir(previous_cwd)
    path_resolution = {
        "checked": len(file_assets),
        "all_exist": all(p is not None and p.exists() for p in first_paths),
        "cwd_independent": [str(p) for p in first_paths] == [str(p) for p in second_paths],
    }

    script = inputs["script"].data
    cta = edit.data.get("cta", {})
    cta_scene = scenes.get(cta.get("scene_id"), {})
    caption = next((c for c in edit.data.get("caption_track", []) if c.get("event_id") == cta.get("caption_event_id")), None)
    cta_check = {
        "is_final_scene": (cta.get("scene_id") == next(reversed(list(scenes))) and abs(cta.get("end", -1) - edit.data.get("total_duration", -1)) < 0.02),
        "caption_matches_script": caption is not None and caption.get("caption_text_reference") == script.get("cta", {}).get("section_id"),
        "audio_matches_script": cta.get("audio_requirement", {}).get("spoken_text") == script.get("cta", {}).get("spoken_text"),
        "visual_present": any(e.get("scene_id") == cta.get("scene_id") and e.get("role") in {"primary_visual", "brand", "diagram", "metric"} for e in edit.data.get("timeline", [])),
    }

    ordered_scenes = [s.get("scene_id") or s.get("id") for s in scene_plan.get("scenes", [])]
    first_by_scene = {}
    for event in sorted(primary_events, key=lambda e: e.get("start", 0)):
        first_by_scene.setdefault(event.get("scene_id"), event)
    boundaries = [first_by_scene[sid].get("transition_in") for sid in ordered_scenes if sid in first_by_scene]
    hard_share = sum(1 for e in primary_events if e.get("transition_in") == "hard_cut") / len(primary_events) if primary_events else 0
    rhythm = {
        "scene_boundary_transitions": boundaries,
        "scene_boundary_diversity": len(set(boundaries)),
        "hard_cut_share_all_primary": round(hard_share, 3),
    }

    coupled = []
    for path in sorted((ROOT / "stages" / "edit").glob("*.py")):
        text = path.read_text(encoding="utf-8")
        hits = [token for token in BANNED_IMPLEMENTATION_TOKENS if token in text]
        if hits:
            coupled.append({"file": path.name, "tokens": hits})

    ok = (
        runtime_match
        and lineage["status"] == "pass"
        and not stale
        and not missing_manifest
        and all(f["valid"] for f in fallbacks)
        and path_resolution["all_exist"]
        and path_resolution["cwd_independent"]
        and all(cta_check.values())
        and not coupled
    )
    return {
        "production_id": production_id,
        "proposal_lock": proposal_lock,
        "proposal_concept": proposal["selected_concept_id"],
        "edit_lock": edit_lock,
        "runtime_lock_source": edit.data.get("runtime_lock_source"),
        "runtime_match": runtime_match,
        "lineage": lineage,
        "stale_artifacts": stale,
        "missing_manifest_assets": missing_manifest,
        "fallbacks": fallbacks,
        "path_resolution": path_resolution,
        "cta": cta_check,
        "rhythm": rhythm,
        "renderer_coupling": coupled,
        "ok": ok,
    }


def print_report(result: dict) -> None:
    print("\nPROPOSAL LOCK")
    print(f"  concept: {result['proposal_concept']}")
    print(f"  {result['proposal_lock']}")
    print("\nEDIT LOCK")
    print(f"  {result['edit_lock']}")
    print(f"  source: {result['runtime_lock_source']}")
    print(f"\nMATCH:\n  {result['runtime_match']}")
    print("\nPARENT ARTIFACTS")
    for finding in result["lineage"]["findings"]:
        print(f"  [{finding['severity']}] {finding['code']}: {finding['evidence']}")
    if not result["lineage"]["findings"]:
        print("  all six locked parents match active versions and hashes")
    print("\nSTALE ARTIFACTS")
    print(f"  {result['stale_artifacts'] or 'none'}")
    print("\nASSET FALLBACKS")
    if not result["fallbacks"]:
        print("  none recorded")
    for fallback in result["fallbacks"]:
        print(f"  {fallback['asset_id']}: {fallback['original_strategy']} -> {fallback['fallback_strategy']}")
        print(f"    reason: {fallback['reason']}")
        print(f"    purpose: {fallback['purpose']} (preserved={fallback['semantic_purpose_preserved']}, resolved={fallback['file_exists_or_native']})")
    print("\nPATH RESOLUTION")
    print(f"  checked={result['path_resolution']['checked']}, all_exist={result['path_resolution']['all_exist']}, cwd_independent={result['path_resolution']['cwd_independent']}")
    print("\nCTA")
    for key, value in result["cta"].items():
        print(f"  {key}={value}")
    print("\nRHYTHM")
    print(f"  scene boundaries={result['rhythm']['scene_boundary_transitions']}")
    print(f"  boundary diversity={result['rhythm']['scene_boundary_diversity']}, hard-cut share={result['rhythm']['hard_cut_share_all_primary']}")
    print("\nRENDERER COUPLING")
    print(f"  {result['renderer_coupling'] or 'none found'}")
    print(f"\nAUDIT OK:\n  {result['ok']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Audit Phase 6 contract integrity for a real production.")
    parser.add_argument("--production", default="proj_0a2bf568")
    args = parser.parse_args()
    report = audit(args.production)
    print_report(report)
    sys.exit(0 if report["ok"] else 1)
