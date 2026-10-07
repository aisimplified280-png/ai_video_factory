from stages.edit.edit_director import EditDirector
from tests.edit_fixtures import inputs, state


def test_timeline_has_no_primary_gaps_and_preserves_relative_scene_shots():
    data = EditDirector().run("edit", state(), inputs()).data
    primary = [e for e in data["timeline"] if e["role"] == "primary_visual"]
    assert [(e["start"], e["end"]) for e in primary] == [(0.0, 3.0), (3.0, 6.0), (6.0, 12.0)]
    assert {e["track_id"] for e in primary} == {"video_primary"}


def test_timeline_converts_absolute_shot_seconds():
    from copy import deepcopy

    bundle = inputs()
    scene = deepcopy(bundle["scene_plan"].data["scenes"][0])
    scene["shots"] = [
        {"shot_id": "absolute_one", "start_seconds": 0.0, "end_seconds": 2.0, "purpose": "absolute establish", "camera_intent": "reveal_space", "motion_intent": "emerge"},
        {"shot_id": "absolute_two", "start_seconds": 2.0, "end_seconds": 6.0, "purpose": "absolute payoff", "camera_intent": "expand_scale", "motion_intent": "flow"},
    ]
    bundle["scene_plan"].data["scenes"][0] = scene
    data = EditDirector().run("edit", state(), bundle).data
    shots = [e for e in data["timeline"] if e["scene_id"] == "scene_01" and e["role"] == "primary_visual"]
    assert [(e["shot_id"], e["start"], e["end"]) for e in shots] == [
        ("absolute_one", 0.0, 2.0),
        ("absolute_two", 2.0, 6.0),
    ]


def test_timeline_selects_purpose_aligned_primary_asset():
    from copy import deepcopy

    bundle = inputs()
    manifest = deepcopy(bundle["asset_manifest"].data)
    manifest["assets"].append({
        "asset_id": "decoy",
        "scene_id": "scene_01",
        "purpose": "Show an unrelated logo",
        "visual_role": "support",
        "type": "logo",
        "source": "native",
        "status": "ready",
        "diagram_spec": {"kind": "logo"},
    })
    bundle["asset_manifest"].data = manifest
    data = EditDirector().run("edit", state(), bundle).data
    assert {e["asset_id"] for e in data["timeline"] if e["scene_id"] == "scene_01" and e["role"] == "primary_visual"} == {"a1"}
    support = next(e for e in data["timeline"] if e["event_id"] == "support_decoy")
    assert support["track_id"] == "video_secondary"
    assert support["role"] == "secondary_visual"
    assert support["z_index"] == 15
    assert support["start"] >= 3.0


def test_timeline_orders_support_layers_above_primary():
    from copy import deepcopy

    bundle = inputs()
    manifest = deepcopy(bundle["asset_manifest"].data)
    manifest["assets"].append({
        "asset_id": "diagram_one",
        "scene_id": "scene_01",
        "purpose": "Diagram the compute engine",
        "visual_role": "support",
        "type": "diagram",
        "source": "native",
        "status": "ready",
        "diagram_spec": {"kind": "engine"},
    })
    bundle["asset_manifest"].data = manifest
    data = EditDirector().run("edit", state(), bundle).data
    support = next(e for e in data["timeline"] if e["event_id"] == "support_diagram_one")
    assert (support["track_id"], support["role"], support["z_index"]) == ("graphics", "diagram", 20)
    assert support["start"] == 3.0
    assert support["caption_ref"] == "caption_scene_01"


def test_timeline_starts_overlay_on_payoff_shot():
    data = EditDirector().run("edit", state(), inputs()).data
    overlay = next(e for e in data["timeline"] if e["event_id"] == "overlay_scene_01")
    assert overlay["start"] == 3.0
    assert overlay["purpose"] == "emphasize reveal"
    assert overlay["audio_ref"] == "sfx_hook_impact"
