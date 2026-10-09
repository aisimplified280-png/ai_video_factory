"""Props builder tests: canonical artifacts project into Remotion props exactly."""
import json
from pathlib import Path

import pytest

from composition.remotion.props_builder import PropsError, build_production_props

PROFILE = {
    "profile": "profiles/youtube_short.json",
    "resolution": {"width": 1080, "height": 1920},
    "fps": 30,
    "duration_constraints": {"minimum_seconds": 10, "maximum_seconds": 60},
    "safe_zones": {"caption": "lower_center_safe", "cta": "center_safe", "brand": "bottom_safe"},
}


def _artifacts(asset_file: str | None = "projects/proj_props/assets/shot.png"):
    edit = {
        "production_id": "proj_props",
        "total_duration": 6.0,
        "platform_profile": "profiles/youtube_short.json",
        "platform": PROFILE,
        "runtime_lock_source": {"artifact_type": "proposal_packet", "version": 1,
                                "content_hash": "sha256:" + "a" * 64, "locked_at": "2026-10-05T00:00:00+00:00",
                                "locked_concept_id": "c1"},
        "renderer_family": "explainer",
        "render_runtime": "remotion",
        "composition_mode": "atelier",
        "timeline": [
            {"event_id": "edit_scene_01_01", "scene_id": "scene_01", "shot_id": "scene_01_shot_01",
             "track_id": "video_primary", "role": "primary_visual", "asset_id": "ast_01",
             "start": 0.0, "end": 3.0, "duration": 3.0, "z_index": 10, "purpose": "Establish the engine",
             "crop": "full_frame", "camera_intent": "reveal_space", "motion_intent": "emerge",
             "transition_in": "fade", "transition_out": None, "caption_ref": "caption_scene_01",
             "audio_ref": "narration_scene_01"},
            {"event_id": "edit_scene_01_02", "scene_id": "scene_01", "shot_id": "scene_01_shot_02",
             "track_id": "video_primary", "role": "primary_visual", "asset_id": "ast_01",
             "start": 3.0, "end": 6.0, "duration": 3.0, "z_index": 10, "purpose": "Inspect the engine",
             "crop": "medium", "camera_intent": "approach_subject", "motion_intent": "assemble",
             "transition_in": "hard_cut", "transition_out": None, "caption_ref": "caption_scene_01",
             "audio_ref": "narration_scene_01"},
        ],
        "video_tracks": {"video_primary": []},
        "audio_tracks": {"narration": [{"event_id": "narration_scene_01", "track_id": "narration",
                                        "start": 0.0, "end": 6.0,
                                        "audio_requirement": {"required": True, "spoken_text": "Hello world engine."},
                                        "purpose": "script narration"}],
                         "music": [], "sfx": []},
        "caption_track": [{"event_id": "caption_scene_01", "scene_id": "scene_01", "start": 0.0, "end": 6.0,
                           "caption_text_reference": "sec_01", "emphasis_words": ["ENGINE"], "safe_zone": "lower_center_safe"}],
        "cta": {"scene_id": "scene_01", "start": 0.0, "end": 6.0, "channel_branding": "AI Simplified Lab",
                "caption_event_id": "caption_scene_01",
                "audio_requirement": {"required": True, "spoken_text": "Subscribe."}},
        "tracks": {"video": []},
    }
    scenes = {"scenes": [{
        "id": "scene_01", "scene_id": "scene_01", "type": "animation", "start_seconds": 0.0, "end_seconds": 6.0,
        "shot_intent": "Establish the engine", "narrative_role": "hook", "subject": "compute engine",
        "visual_purpose": "Establish the engine", "visual_metaphor": "A power grid behaving like an engine.",
        "environment": "a cavern", "depth_strategy": "Layered foreground and background",
        "signature_device_usage": "key_beat", "required_assets": [],
        "shots": [{"shot_id": "scene_01_shot_01"}, {"shot_id": "scene_01_shot_02"}]}],
        "total_duration_seconds": 6.0, "variety_score": 80.0}
    manifest = {"assets": [{
        "asset_id": "ast_01", "scene_id": "scene_01", "purpose": "Establish the engine",
        "visual_role": "primary", "type": "image", "source": "generated", "status": "ready",
        "file_path": asset_file, "subject": "compute engine",
        "diagram_spec": {"nodes": [{"id": "n1", "label": "Engine", "x": 360, "y": 640}], "connectors": []}}],
        "total_estimated_cost": 0.0}
    art = {"design_read": "A deterministic fixture treatment for props.",
           "visual_variance": 8, "motion_intensity": 6, "information_density": 5,
           "palette_discipline": {"primary": "#0F172A", "accent_1": "#38BDF8"},
           "typography_personality": "Direct", "layout_language": "Centered",
           "signature_device": "glow gauge", "anti_patterns": ["No card templates."]}
    script = {"target_duration_seconds": 6, "word_count": 3,
              "sections": [{"id": "sec_01", "section_id": "sec_01", "spoken_text": "Hello world engine.",
                            "narrative_role": "hook"}],
              "cta": {"spoken_text": "Subscribe."}}
    return edit, scenes, manifest, art, script


def _write_asset(tmp_path: Path) -> None:
    target = tmp_path / "projects" / "proj_props" / "assets" / "shot.png"
    target.parent.mkdir(parents=True)
    target.write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * 64)


def test_props_preserve_edit_timing_order_and_refs(tmp_path):
    _write_asset(tmp_path)
    edit, scenes, manifest, art, script = _artifacts()
    props, warnings = build_production_props(
        edit_data=edit, scene_plan_data=scenes, manifest_data=manifest,
        art_direction_data=art, script_data=script, platform_profile=PROFILE,
        projects_root=tmp_path / "projects", public_dir=tmp_path / "public")
    assert [e["event_id"] for e in props["events"]] == ["edit_scene_01_01", "edit_scene_01_02"]
    assert [(e["start"], e["end"]) for e in props["events"]] == [(0.0, 3.0), (3.0, 6.0)]
    assert props["events"][0]["camera_intent"] == "reveal_space"
    assert props["events"][1]["motion_intent"] == "assemble"
    assert props["captions"][0]["textReference"] == "Hello world engine."
    assert props["captions"][0]["emphasisWords"] == ["ENGINE"]
    assert props["lock"]["render_runtime"] == "remotion"
    assert props["cta"]["branding"] == "AI Simplified Lab"
    assert warnings == []


def test_props_carry_native_spec_and_copied_media(tmp_path):
    _write_asset(tmp_path)
    edit, scenes, manifest, art, script = _artifacts()
    props, _ = build_production_props(
        edit_data=edit, scene_plan_data=scenes, manifest_data=manifest,
        art_direction_data=art, script_data=script, platform_profile=PROFILE,
        projects_root=tmp_path / "projects", public_dir=tmp_path / "public")
    assert props["assets"][0]["publicPath"] == "ast_01.png"
    assert (tmp_path / "public" / "assets" / "ast_01.png").is_file()
    assert props["assets"][0]["nativeSpec"]["nodes"][0]["label"] == "Engine"


def test_props_reject_unknown_asset_reference(tmp_path):
    _write_asset(tmp_path)
    edit, scenes, manifest, art, script = _artifacts()
    edit["timeline"][0]["asset_id"] = "ghost"
    with pytest.raises(PropsError):
        build_production_props(
            edit_data=edit, scene_plan_data=scenes, manifest_data=manifest,
            art_direction_data=art, script_data=script, platform_profile=PROFILE,
            projects_root=tmp_path / "projects", public_dir=tmp_path / "public")


def test_props_reject_missing_media_file(tmp_path):
    edit, scenes, manifest, art, script = _artifacts()
    with pytest.raises(PropsError):
        build_production_props(
            edit_data=edit, scene_plan_data=scenes, manifest_data=manifest,
            art_direction_data=art, script_data=script, platform_profile=PROFILE,
            projects_root=tmp_path / "projects", public_dir=tmp_path / "public")


def test_props_reject_asset_without_file_or_native_spec(tmp_path):
    _write_asset(tmp_path)
    edit, scenes, manifest, art, script = _artifacts()
    manifest["assets"][0].pop("file_path")
    manifest["assets"][0].pop("diagram_spec")
    with pytest.raises(PropsError):
        build_production_props(
            edit_data=edit, scene_plan_data=scenes, manifest_data=manifest,
            art_direction_data=art, script_data=script, platform_profile=PROFILE,
            projects_root=tmp_path / "projects", public_dir=tmp_path / "public")


def test_video_declared_still_file_renders_as_image_with_warning(tmp_path):
    _write_asset(tmp_path)
    edit, scenes, manifest, art, script = _artifacts()
    manifest["assets"][0]["type"] = "video"
    props, warnings = build_production_props(
        edit_data=edit, scene_plan_data=scenes, manifest_data=manifest,
        art_direction_data=art, script_data=script, platform_profile=PROFILE,
        projects_root=tmp_path / "projects", public_dir=tmp_path / "public")
    assert props["assets"][0]["kind"] == "image-still"
    assert any("still image" in warning for warning in warnings)


def test_theme_derives_from_art_direction_not_hardcoded(tmp_path):
    _write_asset(tmp_path)
    edit, scenes, manifest, art, script = _artifacts()
    art["palette_discipline"] = {"primary": "#111111", "accent_1": "#222222", "accent_2": "#333333", "neutral": "#444444"}
    props, _ = build_production_props(
        edit_data=edit, scene_plan_data=scenes, manifest_data=manifest,
        art_direction_data=art, script_data=script, platform_profile=PROFILE,
        projects_root=tmp_path / "projects", public_dir=tmp_path / "public")
    assert (props["theme"]["background"], props["theme"]["accent"]) == ("#111111", "#222222")


def test_props_audio_clips_resolve_with_media_server_port(tmp_path, monkeypatch):
    """Verify audio clips in edit_data are converted/staged and resolve port without NameError."""
    _write_asset(tmp_path)
    # Create fake audio asset
    audio_dir = tmp_path / "projects" / "proj_props" / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    audio_file = audio_dir / "narration.wav"
    audio_file.write_bytes(b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00\x88\x58\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00")

    monkeypatch.setenv("MEDIA_SERVER_PORT", "54321")
    edit, scenes, manifest, art, script = _artifacts()
    edit["audio_tracks"]["narration"] = [{
        "event_id": "narr_01",
        "audio_asset_id": "projects/proj_props/audio/narration.wav",
        "start": 0.0,
        "end": 3.0,
        "audio_requirement": {"required": True, "spoken_text": "Narration text"},
    }]
    props, warnings = build_production_props(
        edit_data=edit, scene_plan_data=scenes, manifest_data=manifest,
        art_direction_data=art, script_data=script, platform_profile=PROFILE,
        projects_root=tmp_path / "projects", public_dir=tmp_path / "public")

    assert len(props["audio"]) == 1
    assert props["audio"][0]["publicPath"] == "http://127.0.0.1:54321/narr_01.wav"


def _scene(scene_id: str, start: float, end: float, role: str, subject: str) -> dict:
    return {
        "id": scene_id, "scene_id": scene_id, "type": "animation",
        "start_seconds": start, "end_seconds": end,
        "shot_intent": subject, "narrative_role": role, "subject": subject,
        "visual_purpose": subject, "visual_metaphor": "",
        "environment": "a cavern", "depth_strategy": None,
        "signature_device_usage": "none", "required_assets": [],
    }


def test_milestone_tabs_derive_from_content_scenes(tmp_path):
    """Top milestone bar: chapter tabs from content scenes, CTA excluded, short labels."""
    _write_asset(tmp_path)
    edit, scenes, manifest, art, script = _artifacts()
    scenes["scenes"] = [
        _scene("scene_01", 0.0, 4.0, "hook", "How do RAGs retrieve answers?"),
        _scene("scene_02", 4.0, 8.0, "body", "Then the model chunks the documents"),
        _scene("scene_03", 8.0, 12.0, "body", "Vector search finds the match"),
        _scene("scene_04", 12.0, 16.0, "cta", "AI Simplified Lab"),
    ]
    edit["cta"] = {**edit["cta"], "scene_id": "scene_04", "start": 12.0, "end": 16.0}
    props, _ = build_production_props(
        edit_data=edit, scene_plan_data=scenes, manifest_data=manifest,
        art_direction_data=art, script_data=script, platform_profile=PROFILE,
        projects_root=tmp_path / "projects", public_dir=tmp_path / "public")

    milestones = props["milestones"]
    assert [m["scene_id"] for m in milestones] == ["scene_01", "scene_02", "scene_03"]
    labels = [m["label"] for m in milestones]
    # Question scaffolding is stripped; every label is tab-sized.
    assert labels[0] == "RAGs retrieve…"
    assert all(isinstance(label, str) and label and len(label) <= 16 for label in labels)
    # scene_01's span is event-derived (the fixture's events end at 6.0).
    assert [(m["start"], m["end"]) for m in milestones] == [(0.0, 6.0), (4.0, 8.0), (8.0, 12.0)]


def test_no_milestone_tabs_without_two_content_scenes(tmp_path):
    """A lone scene (the single-scene fixture is its own CTA) never shows a one-tab bar."""
    _write_asset(tmp_path)
    edit, scenes, manifest, art, script = _artifacts()
    props, _ = build_production_props(
        edit_data=edit, scene_plan_data=scenes, manifest_data=manifest,
        art_direction_data=art, script_data=script, platform_profile=PROFILE,
        projects_root=tmp_path / "projects", public_dir=tmp_path / "public")
    assert props["milestones"] == []

