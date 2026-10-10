"""Sync honesty + motion ownership proven against the REAL sync pipeline (§5, §9, §10).

Runs sync_authoritative_artifacts on a temporary fixture and asserts:
- validation flags are MEASURED: genuinely-missing asset files flip
  all_assets_resolved to False (the old code hardcoded True for all eight);
  existing narration files are what make audio_valid True.
- variety_score is computed from the plan and carries its measurement basis —
  never the old fixed 9.9.
- the live timeline contains NO per-scene background events (the constant
  canvas renders instead) and motion_intent is null by default: only diagram
  midground elements receive "assemble" (element choreography).
- the diagram spec carries the semantic fields the renderer needs
  (shape_style / node_type / icon / relationship / topology).
- background PNGs remain registered but clearly labelled as not rendered.
"""
from pathlib import Path

from production.artifact_store import ArtifactStore
from production.state import StateStore
from production.phase17.style_systems import get_style_system
from production.phase18.sync import sync_authoritative_artifacts
from production.phase18.visual_director import direct_production_scenes
from schemas.models.artifact import ProducerInfo
from schemas.models.common import ProducerKind

GPS_NARRATION = (
    "GPS satellites send precise timing signals to your phone. "
    "The phone compares four arrival times to fix its position."
)


def _seed_store(store: ArtifactStore, prod_id: str) -> tuple:
    script_payload = {
        "title": "How GPS Works",
        "hook": "How GPS works.",
        "target_duration_seconds": 30.0,
        "word_count": 40,
        "sections": [
            {
                "id": "sec_01",
                "narrative_role": "mechanism",
                "spoken_text": GPS_NARRATION,
                "estimated_start": 0.0,
                "estimated_end": 5.0,
                "duration": 5.0,
                "visual_intent": "Satellites sending timing signals to a phone",
                "primary_intent": "reveal",
                "primary_subject": "GPS positioning",
                "emphasis_words": ["satellites", "phone"],
            },
            {
                "id": "sec_02",
                "narrative_role": "cta",
                "spoken_text": "Subscribe for more.",
                "estimated_start": 5.0,
                "estimated_end": 8.0,
                "duration": 3.0,
                "visual_intent": "Closing call to action",
                "primary_intent": "convert",
                "primary_subject": "Subscribe",
                "emphasis_words": ["subscribe"],
            },
        ],
    }
    script_env = store.create(
        "script", prod_id, "script", script_payload,
        producer=ProducerInfo(kind=ProducerKind.SYSTEM, provider="test"),
    )
    store.save(script_env)
    store.approve("script", prod_id, script_env.artifact_version)

    concept = {
        "concept_id": "c1", "title": "GPS Breakdown", "concept_family": "explainer",
        "hook": "GPS breakdown", "audience_promise": "Promise", "narrative_structure": "Structure",
        "visual_direction": "Editorial", "visual_metaphor": "Satellites", "tone": "Technical",
        "pacing": "Fast", "scene_grammar": "HUD", "renderer_family": "explainer",
        "render_runtime": "remotion", "composition_mode": "atelier", "asset_strategy": "vector",
        "target_duration": 30.0, "reasoning": "Reasoning",
    }
    concept2 = dict(concept, concept_id="c2", title="GPS Deep Dive", hook="GPS deep dive")
    proposal_payload = {
        "selected_concept_id": "c1",
        "concepts": [concept, concept2],
        "decision_log": {
            "selected_concept_id": "c1", "decision_reason": "Default",
            "selection_mode": "auto", "timestamp": "2026-10-08T00:00:00Z", "actor": "system",
        },
    }
    proposal_env = store.create(
        "proposal_packet", prod_id, "proposal", proposal_payload,
        producer=ProducerInfo(kind=ProducerKind.SYSTEM, provider="test"),
    )
    store.save(proposal_env)
    store.approve("proposal_packet", prod_id, proposal_env.artifact_version)
    return script_env, proposal_env


def _run_sync(tmp_path: Path, prod_id: str):
    store = ArtifactStore(tmp_path / "artifacts")
    state_store = StateStore(projects_root=tmp_path / "projects")
    state = state_store.create(
        project_id=prod_id, pipeline="youtube-short", pipeline_version="2.0", target_duration=30.0,
    )
    script_env, proposal_env = _seed_store(store, prod_id)

    sections = [
        {"section_id": "sec_01", "narrative_role": "mechanism", "spoken_text": GPS_NARRATION,
         "emphasis_words": ["satellites", "phone"]},
        {"section_id": "sec_02", "narrative_role": "context", "spoken_text": "Subscribe for more.",
         "emphasis_words": ["subscribe"]},
    ]
    plan = direct_production_scenes(prod_id, sections, "How GPS works", [5.0, 3.0])

    # Narration files exist before sync — audio_valid must reflect reality.
    audio_dir = tmp_path / "projects" / prod_id / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    for sc in plan.scenes:
        (audio_dir / f"narration_{sc.scene_id}.mp3").write_bytes(b"ID3fake")

    edit_data = sync_authoritative_artifacts(
        store=store,
        state=state,
        visual_plan=plan,
        script_envelope=script_env,
        proposal_envelope=proposal_env,
        style_system=get_style_system("claude_editorial"),
        projects_root=tmp_path / "projects",
    )
    return store, plan, edit_data


def test_validation_flags_are_measured_not_hardcoded(tmp_path: Path):
    store, _plan, edit_data = _run_sync(tmp_path, "prod_val_test")
    v = edit_data["validation"]

    # Missing on disk (never generated in this fixture) → False. The old code
    # hardcoded True for every flag.
    assert v["all_assets_resolved"] is False, "asset PNGs do not exist — flag must reflect that"
    # projects_root.parent is tmp_path: no composer there → measured False.
    assert v["renderer_locked"] is False, "no pinned composer under tmp — flag must reflect that"
    # Real narration files → True (measured from disk, both directions covered).
    assert v["audio_valid"] is True
    # Director output is contiguous and covers exactly the plan duration.
    assert v["no_gaps"] is True
    assert v["no_overlaps"] is True
    assert v["duration_covered"] is True
    assert v["captions_valid"] is True
    # Last section input role was "context" — normalized CTA role makes this True.
    assert v["cta_present"] is True


def test_variety_score_is_computed_from_the_plan(tmp_path: Path):
    store, plan, _edit = _run_sync(tmp_path, "prod_variety_test")
    scene_plan = store.load("scene_plan", "prod_variety_test").data
    measure = scene_plan["variety_measure"]
    assert measure["scene_count"] == len(plan.scenes)
    assert measure["node_label_count"] > 0
    expected = round(
        100.0 * (
            0.5 * measure["distinct_topologies"] / measure["scene_count"]
            + 0.5 * measure["distinct_node_labels"] / measure["node_label_count"]
        ),
        1,
    )
    assert scene_plan["variety_score"] == expected
    assert scene_plan["variety_score"] != 9.9, "fixed 9.9 must be gone"


def test_timeline_has_no_background_events_and_static_default(tmp_path: Path):
    _store, _plan, edit_data = _run_sync(tmp_path, "prod_motion_test")

    timeline = edit_data["multi_layer_timeline"]
    assert timeline, "expected timeline events"
    # §10: per-scene backgrounds are out of the live timeline entirely.
    assert all(e["role"] != "background" for e in timeline)
    assert edit_data["video_tracks"]["video_bg"] == [], "background track must be empty"
    # Manifest still registers the PNGs, explicitly labelled not-rendered.
    # (checked in test_manifest_labels_background_as_diagnostic below)

    # §5 static default: motion_intent is null unless the element is a diagram
    # midground being choreographed in sequence.
    diagram_mid_seen = False
    for e in timeline:
        if e["role"] == "midground" and e.get("motion_intent"):
            assert e["motion_intent"] == "assemble", e
            diagram_mid_seen = True
        else:
            assert e.get("motion_intent") is None, (
                f"forced motion on {e['role']}: {e.get('motion_intent')}"
            )
    assert diagram_mid_seen, "the GPS flow scene should get an assembling diagram"


def test_manifest_labels_background_as_diagnostic_and_keeps_semantics(tmp_path: Path):
    store, _plan, _edit = _run_sync(tmp_path, "prod_manifest_test")
    manifest = store.load("asset_manifest", "prod_manifest_test").data

    bg_assets = [a for a in manifest["assets"] if a.get("role") == "background"]
    assert bg_assets, "background PNGs remain registered as diagnostics"
    assert all(a["rendered_in_timeline"] is False for a in bg_assets)
    assert all(a["rendered_in_timeline"] for a in manifest["assets"] if a["role"] != "background")

    # The GPS flow scene's diagram spec survives graph → sync with semantics.
    diagrams = [a for a in manifest["assets"] if a.get("diagram_spec")]
    assert diagrams, "expected a native diagram for the process_flow scene"
    spec = diagrams[0]["diagram_spec"]
    assert spec["topology"] == "process_flow"
    assert any(n.get("icon") for n in spec["nodes"]), "node icons must reach the renderer"
    assert any(n.get("shape_style") for n in spec["nodes"]), "shape styles must reach the renderer"
    assert any(n.get("node_type") for n in spec["nodes"]), "node types must reach the renderer"
    assert any(c.get("relationship") for c in spec["connectors"]), "edge relationships must reach the renderer"
