from datetime import datetime, timezone

from production.artifact_store import ArtifactStore
from schemas.models.artifact import ArtifactEnvelope, ProducerInfo
from schemas.models.common import ArtifactStatus, ProducerKind, RunMode
from schemas.models.production import ProductionState


def state():
    now = datetime.now(timezone.utc)
    return ProductionState(project_id="edit_fixture", pipeline="youtube-short", pipeline_version="2.0", run_mode=RunMode.AUTO, target_duration=12, aspect_ratio="9:16", platform="youtube_shorts", created_at=now, updated_at=now)


def envelope(kind, data, production_id="edit_fixture"):
    now = datetime.now(timezone.utc)
    return ArtifactEnvelope(artifact_type=kind, artifact_version=1, production_id=production_id, stage="assets" if kind == "asset_manifest" else kind, status=ArtifactStatus.READY, created_at=now, updated_at=now, producer=ProducerInfo(kind=ProducerKind.SYSTEM), content_hash=ArtifactStore.compute_hash(data), data=data)


def _proposal_concept(concept_id, renderer_family):
    return {
        "concept_id": concept_id,
        "hook": f"Deterministic test hook for {concept_id}",
        "audience_promise": "A deterministic edit contract.",
        "narrative_structure": "Hook then CTA",
        "visual_direction": "Deterministic editorial fixture",
        "tone": "Direct",
        "target_duration": 12.0,
        "renderer_family": renderer_family,
        "render_runtime": "remotion",
        "composition_mode": "atelier",
    }


def inputs(production_id="edit_fixture"):
    sections = [
        {"id": "s1", "section_id": "s1", "start_seconds": 0, "end_seconds": 6, "spoken_text": "A big idea begins with a simple visual shift.", "narrative_role": "hook", "emphasis_words": ["big", "shift"]},
        {"id": "s2", "section_id": "s2", "start_seconds": 6, "end_seconds": 12, "spoken_text": "Subscribe to AI Simplified Lab for more breakdowns.", "narrative_role": "cta", "emphasis_words": ["Subscribe"]},
    ]
    scenes = [
        {"id": "scene_01", "scene_id": "scene_01", "type": "animation", "start_seconds": 0, "end_seconds": 6, "script_section_id": "s1", "shot_intent": "Establish the central mechanism", "narrative_role": "hook", "visual_purpose": "Establish the central mechanism", "subject": "compute engine", "continuity_to_next": "The engine powers the brand mark.", "camera_intent": "approach_subject", "motion_intent": "assemble", "shots": [{"shot_id": "scene_01_shot_01", "start": 0, "end": 3, "purpose": "establish", "camera_intent": "reveal_space", "motion_intent": "emerge"}, {"shot_id": "scene_01_shot_02", "start": 3, "end": 6, "purpose": "reveal", "camera_intent": "approach_subject", "motion_intent": "assemble"}], "required_assets": [{"asset_type": "native_composition", "purpose": "Show compute engine", "visual_role": "primary"}]},
        {"id": "scene_02", "scene_id": "scene_02", "type": "text_card", "start_seconds": 6, "end_seconds": 12, "script_section_id": "s2", "shot_intent": "Convert attention into subscription", "narrative_role": "cta", "visual_purpose": "Convert attention into subscription", "subject": "AI Simplified Lab", "continuity_from_previous": "The engine powers the brand mark.", "camera_intent": "observe_static", "motion_intent": "pulse", "shots": [{"shot_id": "scene_02_shot_01", "start": 0, "end": 6, "purpose": "brand payoff", "camera_intent": "observe_static", "motion_intent": "pulse"}], "required_assets": [{"asset_type": "native_composition", "purpose": "Show channel brand", "visual_role": "primary"}]},
    ]
    proposal = {
        "selected_concept_id": "c1",
        "concepts": [_proposal_concept("c1", "explainer"), _proposal_concept("c2", "cinematic")],
        "decision_log": {
            "selected_concept_id": "c1",
            "decision_reason": "Deterministic fixture locks the explainer runtime.",
            "selection_mode": "auto",
            "timestamp": "2026-10-05T00:00:00+00:00",
            "actor": "system",
            "rejected_concepts": ["c2"],
            "locked_decisions": {"renderer_family": "explainer", "render_runtime": "remotion", "composition_mode": "atelier"},
        },
    }
    research = {"topic": "Deterministic edit fixture", "audience": "Fixture reviewers", "sources": [{"title": "Fixture source", "url": "https://example.org/fixture"}], "facts": ["A deterministic fixture supports edit tests."], "angles_discovered": ["A minimal upstream chain can prove edit behavior."]}
    art_direction = {"design_read": "A deterministic high-contrast fixture treatment.", "visual_variance": 8, "motion_intensity": 6, "information_density": 5, "palette_discipline": {"primary": "#0F172A", "accent_1": "#38BDF8"}, "typography_personality": "Direct fixture type", "layout_language": "Centered fixture layout", "signature_device": "glow gauge", "anti_patterns": ["Do not use card templates."]}
    script = {"target_duration_seconds": 12, "estimated_duration_seconds": 12, "word_count": 18, "sections": sections, "cta": {"spoken_text": sections[-1]["spoken_text"]}}
    scene_plan = {"scenes": scenes, "total_duration_seconds": 12, "variety_score": 80.0}
    assets = {"assets": [{"asset_id": "a1", "scene_id": "scene_01", "purpose": "Show compute engine", "visual_role": "primary", "type": "native_composition", "source": "native", "status": "ready", "diagram_spec": {"kind": "engine"}}, {"asset_id": "a2", "scene_id": "scene_02", "purpose": "Show channel brand", "visual_role": "primary", "type": "native_composition", "source": "native", "status": "ready", "diagram_spec": {"kind": "brand"}}], "total_estimated_cost": 0.0}
    return {"research_brief": envelope("research_brief", research, production_id), "proposal_packet": envelope("proposal_packet", proposal, production_id), "art_direction": envelope("art_direction", art_direction, production_id), "script": envelope("script", script, production_id), "scene_plan": envelope("scene_plan", scene_plan, production_id), "asset_manifest": envelope("asset_manifest", assets, production_id)}
