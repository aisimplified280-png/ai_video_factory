"""Render manifest tests: only executed work is recorded."""
from composition.remotion.renderer import build_render_manifest


def test_manifest_lists_only_executed_operations():
    manifest = build_render_manifest({
        "production_id": "proj_local", "edit_artifact_version": 1,
        "edit_artifact_hash": "sha256:" + "a" * 64, "runtime": "remotion",
        "renderer_family": "cinematic", "composition_mode": "atelier",
        "shots_executed": ["scene_01_shot_01"], "assets_executed": ["ast_01"],
        "motions_executed": ["emerge"], "camera_operations": ["reveal_space"],
        "transitions_executed": ["fade"], "captions_executed": ["caption_scene_01"],
        "audio_tracks": [], "cta_executed": True, "warnings": ["w1"], "errors": [],
    })
    assert manifest["shots_executed"] == ["scene_01_shot_01"]
    assert "transform" not in manifest["motions_executed"]
    assert manifest["cta_executed"] is True
    assert manifest["warnings"] == ["w1"]
    assert manifest["runtime"] == "remotion"


def test_manifest_defaults_to_empty_not_invented():
    manifest = build_render_manifest({})
    assert manifest["shots_executed"] == []
    assert manifest["assets_executed"] == []
    assert manifest["cta_executed"] is False
    assert manifest["errors"] == []
