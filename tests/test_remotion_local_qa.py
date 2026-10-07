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
    stats = qa._frame_stats(busy)
    assert stats["stddev"] > 12
