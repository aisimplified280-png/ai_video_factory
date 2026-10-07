"""Audio tests: declared references embed; missing files fail loudly."""
from pathlib import Path

import pytest

from composition.remotion.props_builder import PropsError, build_production_props
from test_remotion_props import PROFILE, _artifacts, _write_asset


def test_deferred_audio_carries_requirement_without_file(tmp_path):
    _write_asset(tmp_path)
    edit, scenes, manifest, art, script = _artifacts()
    props, _ = build_production_props(
        edit_data=edit, scene_plan_data=scenes, manifest_data=manifest,
        art_direction_data=art, script_data=script, platform_profile=PROFILE,
        projects_root=tmp_path / "projects", public_dir=tmp_path / "public")
    narration = next(clip for clip in props["audio"] if clip["track"] == "narration")
    assert narration["publicPath"] is None
    assert narration["requirement"]["spoken_text"] == "Hello world engine."


def test_referenced_but_missing_audio_file_blocks_props(tmp_path):
    _write_asset(tmp_path)
    edit, scenes, manifest, art, script = _artifacts()
    edit["audio_tracks"]["narration"][0]["audio_asset_id"] = "projects/proj_props/assets/missing.mp3"
    with pytest.raises(PropsError):
        build_production_props(
            edit_data=edit, scene_plan_data=scenes, manifest_data=manifest,
            art_direction_data=art, script_data=script, platform_profile=PROFILE,
            projects_root=tmp_path / "projects", public_dir=tmp_path / "public")


def test_no_silent_audio_placeholders_in_composer():
    text = (Path(__file__).resolve().parent.parent / "remotion-composer" / "src"
            / "compositions" / "SceneComposition.tsx").read_text(encoding="utf-8")
    assert "silent" not in text.lower()
