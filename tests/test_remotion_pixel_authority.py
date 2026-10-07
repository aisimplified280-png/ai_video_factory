"""Pixel-authority tests: the frame comparator that judges render-level changes."""
from PIL import Image

from composition.remotion.renderer import compare_frames, frames_differ


def _frame(path, color, size=(64, 36)):
    Image.new("RGB", size, color).save(path)


def test_identical_frames_measure_zero(tmp_path):
    first, second = tmp_path / "a.png", tmp_path / "b.png"
    _frame(first, (10, 20, 30))
    _frame(second, (10, 20, 30))
    assert compare_frames(first, second) == 0.0
    assert frames_differ(first, second) is False


def test_changed_frames_measure_above_threshold(tmp_path):
    first, second = tmp_path / "a.png", tmp_path / "b.png"
    _frame(first, (10, 20, 30))
    _frame(second, (200, 20, 30))
    assert compare_frames(first, second) > 1.0
    assert frames_differ(first, second) is True


def test_encoding_noise_below_threshold_counts_as_same(tmp_path):
    first, second = tmp_path / "a.png", tmp_path / "b.png"
    _frame(first, (10, 20, 30))
    _frame(second, (11, 20, 30))
    assert frames_differ(first, second, threshold=5.0) is False
