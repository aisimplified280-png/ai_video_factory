"""Caption tests: edit references execute; timing is never regenerated."""
from pathlib import Path

import pytest

from composition.remotion.props_builder import PropsError, build_production_props
from test_remotion_props import PROFILE, _artifacts, _write_asset

COMPOSER = Path(__file__).resolve().parent.parent / "remotion-composer" / "src"


def test_caption_text_resolves_from_script_sections(tmp_path):
    _write_asset(tmp_path)
    edit, scenes, manifest, art, script = _artifacts()
    props, _ = build_production_props(
        edit_data=edit, scene_plan_data=scenes, manifest_data=manifest,
        art_direction_data=art, script_data=script, platform_profile=PROFILE,
        projects_root=tmp_path / "projects", public_dir=tmp_path / "public")
    assert props["captions"][0]["textReference"] == "Hello world engine."
    assert props["captions"][0]["start"] == 0.0
    assert props["captions"][0]["end"] == 6.0


def test_caption_track_supports_all_modes_in_code():
    text = (COMPOSER / "captions" / "CaptionTrack.tsx").read_text(encoding="utf-8")
    for mode in ("sentence", "word_highlight", "karaoke", "emphasis_words"):
        assert mode in text, mode


def test_caption_timing_comes_from_props_not_regenerated():
    text = (COMPOSER / "captions" / "CaptionTrack.tsx").read_text(encoding="utf-8")
    assert "eventFrames(caption.start, caption.end" in text
    assert "spoken_text" not in text
