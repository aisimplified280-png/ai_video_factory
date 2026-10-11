"""QA helper tests on synthetic frames (no render required)."""
import importlib.util
import sys
from pathlib import Path

from PIL import Image


def _qa_module():
    path = Path(__file__).resolve().parent.parent / "scripts" / "run_local_production.py"
    spec = importlib.util.spec_from_file_location("run_local_production", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["run_local_production"] = module
    spec.loader.exec_module(module)
    return module


def test_frame_stats_detects_black(tmp_path):
    qa = _qa_module()
    black = tmp_path / "black.png"
    Image.new("RGB", (64, 36), (0, 0, 0)).save(black)
    assert qa._frame_stats(black)["mean"] < 8


def test_frame_stats_detects_blank(tmp_path):
    qa = _qa_module()
    blank = tmp_path / "blank.png"
    Image.new("RGB", (64, 36), (128, 128, 128)).save(blank)
    stats = qa._frame_stats(blank)
    assert stats["stddev"] < 3 and 20 < stats["mean"] < 235


def test_frame_stats_detects_content(tmp_path):
    qa = _qa_module()
    busy = tmp_path / "busy.png"
    img = Image.new("RGB", (64, 36), (10, 10, 10))
    img.paste(Image.new("RGB", (32, 36), (240, 240, 240)), (16, 0))
    img.save(busy)
    assert qa._frame_stats(busy)["stddev"] > 12


def test_visual_activity_identical_frames_is_zero(tmp_path):
    qa = _qa_module()
    a, b = tmp_path / "a.png", tmp_path / "b.png"
    Image.new("RGB", (64, 36), (120, 120, 120)).save(a)
    Image.new("RGB", (64, 36), (120, 120, 120)).save(b)
    hist, spat = qa._visual_activity([a, b])
    assert hist == 0.0 and spat == 0.0


def test_visual_activity_spatial_catches_motion_histogram_cannot_see(tmp_path):
    """Translation with identical luminance histograms: histogram=0, spatial>0."""
    qa = _qa_module()
    a, b = tmp_path / "left.png", tmp_path / "right.png"
    left = Image.new("RGB", (64, 36), (10, 10, 10))
    left.paste(Image.new("RGB", (16, 36), (240, 240, 240)), (0, 0))
    left.save(a)
    right = Image.new("RGB", (64, 36), (10, 10, 10))
    right.paste(Image.new("RGB", (16, 36), (240, 240, 240)), (48, 0))
    right.save(b)
    hist, spat = qa._visual_activity([a, b])
    assert hist == 0.0, "histograms are identical even though the frame visibly changed"
    assert spat > 0.10, "the spatial term must see the moved block"


def test_visual_activity_tonal_change_raises_histogram(tmp_path):
    qa = _qa_module()
    a, b = tmp_path / "dim.png", tmp_path / "bright.png"
    Image.new("RGB", (64, 36), (60, 60, 60)).save(a)
    Image.new("RGB", (64, 36), (200, 200, 200)).save(b)
    hist, spat = qa._visual_activity([a, b])
    assert hist > 0.5 and spat > 0.4


def test_activity_gate_applies_only_when_plan_requires_motion():
    """The floors bind plans that declare motion; fully static plans are
    governed by freeze_check instead (P1: no unconditional activity floor)."""
    qa = _qa_module()
    static_edit = {"timeline": [
        {"event_id": "e1", "role": "midground", "motion_intent": None, "camera_intent": "static"},
        {"event_id": "e2", "role": "character", "motion_intent": None, "camera_intent": None,
         "character_spec": {"motion": "static"}},
    ], "multi_layer_timeline": []}
    applies, reason = qa.activity_gate_applies(static_edit)
    assert applies is False, reason

    for event in (
        {"event_id": "d", "role": "midground", "motion_intent": "assemble", "camera_intent": "static"},
        {"event_id": "c", "role": "midground", "motion_intent": None, "camera_intent": "push_in"},
        {"event_id": "m", "role": "character", "motion_intent": None, "camera_intent": None,
         "character_spec": {"motion": "stride"}},
    ):
        applies, reason = qa.activity_gate_applies({"timeline": [event], "multi_layer_timeline": []})
        assert applies is True, (event, reason)

    # The multi-layer timeline is scanned too, not just the primary track.
    applies, _ = qa.activity_gate_applies({
        "timeline": [], "multi_layer_timeline": [{"event_id": "x", "camera_intent": "tracking"}]})
    assert applies is True
