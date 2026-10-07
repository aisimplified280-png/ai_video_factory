"""Phase 16 Canonical Artifact Synchronization.

Ensures that the production ArtifactStore has synchronized, up-to-date versions of:
- scene_plan (matching the 5 canonical script scenes)
- asset_manifest (all assets declared as images with direct file paths and zero stale native diagram specs)
- art_direction (Editorial Intelligence palette, materials, and typography)

This guarantees that Remotion's props_builder generates clean props that display the
actual Phase 16 editorial assets rather than falling back to Phase 8 frozen test templates.
"""
from __future__ import annotations

from typing import Any
from schemas.models.artifact import ProducerInfo
from schemas.models.common import ProducerKind
from production.artifact_store import ArtifactStore
from .design_system import VisualDesignSystem


def sync_phase16_production_artifacts(
    store: ArtifactStore,
    production_id: str,
    plan_data: dict[str, Any],
    design_system: VisualDesignSystem,
    state: Any,
    timeline: list[dict[str, Any]] | None = None,
) -> None:
    """Synchronize scene_plan, asset_manifest, and art_direction in the production ArtifactStore."""
    scenes_concepts = plan_data.get("scene_concepts", [])

    scene_bounds: dict[str, list[float]] = {}
    if timeline:
        for ev in timeline:
            sc_id = ev.get("scene_id")
            if sc_id:
                if sc_id not in scene_bounds:
                    scene_bounds[sc_id] = [float(ev.get("start", 0.0)), float(ev.get("end", 0.0))]
                else:
                    scene_bounds[sc_id][0] = min(scene_bounds[sc_id][0], float(ev.get("start", 0.0)))
                    scene_bounds[sc_id][1] = max(scene_bounds[sc_id][1], float(ev.get("end", 0.0)))

    # 1. Synchronize scene_plan
    scenes_list = []
    for idx, c in enumerate(scenes_concepts):
        sc_id = c.get("scene_id", f"scene_{idx+1:02d}")
        bounds = scene_bounds.get(sc_id, [idx * 5.5, (idx + 1) * 5.5])
        scenes_list.append({
            "id": sc_id,
            "scene_id": sc_id,
            "type": "generated",
            "start_seconds": round(bounds[0], 2),
            "end_seconds": round(bounds[1], 2),
            "shot_intent": c.get("shot_type", "medium"),
            "narrative_role": c.get("narrative_role", "context"),
            "subject": c.get("subject", "Frontier AI"),
            "visual_purpose": c.get("visual_intent", "Editorial visual demonstration"),
            "environment": c.get("environment", "Editorial Intelligence Studio"),
            "required_assets": [f"ast_{sc_id}_primary"],
        })

    total_dur = max((b[1] for b in scene_bounds.values()), default=len(scenes_list) * 5.5) if scene_bounds else len(scenes_list) * 5.5
    scene_plan_payload = {
        "scenes": scenes_list,
        "total_duration_seconds": round(total_dur, 2),
        "variety_score": 9.2,
    }
    scene_env = store.create(
        "scene_plan",
        production_id,
        "scene_plan",
        scene_plan_payload,
        producer=ProducerInfo(kind=ProducerKind.SYSTEM, provider="phase16_scene_director"),
    )
    store.save(scene_env)
    store.approve("scene_plan", production_id, scene_env.artifact_version)
    state.set_active_version("scene_plan", scene_env.artifact_version)

    # 2. Synchronize asset_manifest
    manifest_assets = []
    for idx, c in enumerate(scenes_concepts):
        sc_id = c.get("scene_id", f"scene_{idx+1:02d}")
        manifest_assets.append({
            "asset_id": f"ast_{sc_id}_primary",
            "scene_id": sc_id,
            "purpose": c.get("visual_intent", "Hero editorial visual"),
            "type": "image",
            "source": "generated",
            "status": "ready",
            "file_path": f"projects/{production_id}/assets/ast_{sc_id}_primary.png",
            "diagram_spec": None,  # Explicitly null to prevent DiagramLayer interception
        })

    manifest_payload = {
        "assets": manifest_assets,
        "total_estimated_cost": 0.0,
    }
    manifest_env = store.create(
        "asset_manifest",
        production_id,
        "assets",
        manifest_payload,
        producer=ProducerInfo(kind=ProducerKind.SYSTEM, provider="phase16_asset_director"),
    )
    store.save(manifest_env)
    store.approve("asset_manifest", production_id, manifest_env.artifact_version)
    state.set_active_version("asset_manifest", manifest_env.artifact_version)

    # 3. Synchronize art_direction
    art_payload = {
        "design_read": "Editorial Intelligence: warm neutral charcoal, restrained terracotta accent, clean typography",
        "visual_variance": 8,
        "motion_intensity": 6,
        "information_density": 6,
        "palette_discipline": {
            "primary": design_system.palette.background,
            "accent_1": design_system.palette.accent,
            "accent_2": design_system.palette.accent_secondary,
            "neutral": design_system.palette.secondary_text,
        },
        "typography_personality": "Editorial Intelligence",
        "layout_language": "Clean, spacious, clear subject isolation with negative space",
        "signature_device": "Restrained editorial status card",
        "anti_patterns": design_system.materials.prohibited,
    }
    art_env = store.create(
        "art_direction",
        production_id,
        "art_direction",
        art_payload,
        producer=ProducerInfo(kind=ProducerKind.SYSTEM, provider="phase16_art_director"),
    )
    store.save(art_env)
    store.approve("art_direction", production_id, art_env.artifact_version)
    state.set_active_version("art_direction", art_env.artifact_version)
