"""Unit and regression tests for complete final-video QA coverage.

Validates:
1. Sampling derived from actual duration without fixed-duration ceiling.
2. Complete duration coverage for 90s videos (including samples >= 89.9s).
3. Explicit coverage of deciles (0%, 10%, ..., 100%).
4. Coverage of every scene boundary and transition window.
5. Coverage of CTA window and final frame.
"""
from __future__ import annotations

import pytest
from scripts.qa_editorial_video import compute_sample_times


def test_qa_sampling_covers_90s_video_without_ceiling():
    """Verify that a 90-second video has late-video sampling near 90 seconds without ceiling."""
    duration = 90.0
    samples = compute_sample_times(duration, step=3.0)

    # Must contain samples across the whole 90 seconds
    assert len(samples) > 30
    assert min(samples) == 0.0
    assert max(samples) >= 89.9
    # Verify late-video coverage
    late_samples = [s for s in samples if s >= 80.0]
    assert len(late_samples) >= 4, f"Expected multiple late-video samples >= 80s, got {late_samples}"
    assert any(s >= 89.0 for s in samples), "Missing final-window sample near 90s"


def test_qa_sampling_includes_all_deciles():
    """Verify that all deciles 0%, 10%, 20%, ..., 100% are explicitly included."""
    duration = 60.0
    samples = compute_sample_times(duration)

    expected_deciles = [0.0, 6.0, 12.0, 18.0, 24.0, 30.0, 36.0, 42.0, 48.0, 54.0]
    for d in expected_deciles:
        assert any(abs(s - d) < 0.01 for s in samples), f"Missing decile {d}s in samples"
    # Final decile near duration
    assert any(abs(s - (duration - 0.05)) < 0.1 for s in samples)


def test_qa_sampling_covers_scene_boundaries_and_transition_windows():
    """Verify that scene boundaries and transition windows (+/- 0.25s) are sampled."""
    duration = 45.0
    scenes = [
        {"scene_id": "scene_01", "start_seconds": 0.0, "end_seconds": 12.0},
        {"scene_id": "scene_02", "start_seconds": 12.0, "end_seconds": 25.0},
        {"scene_id": "scene_03", "start_seconds": 25.0, "end_seconds": 38.0},
        {"scene_id": "scene_04", "start_seconds": 38.0, "end_seconds": 45.0},
    ]

    samples = compute_sample_times(duration, scenes=scenes)

    # Boundaries: 12.0, 25.0, 38.0
    for boundary in [12.0, 25.0, 38.0]:
        assert any(abs(s - boundary) < 0.01 for s in samples), f"Missing boundary {boundary} in samples"
        # Transition window: boundary + 0.25
        assert any(abs(s - (boundary + 0.25)) < 0.01 for s in samples), f"Missing transition window {boundary + 0.25} in samples"


def test_qa_sampling_covers_cta_window():
    """Verify that CTA window start and midpoint are included in samples."""
    duration = 30.0
    cta_window = (24.0, 30.0)
    samples = compute_sample_times(duration, cta_window=cta_window)

    assert any(abs(s - 24.0) < 0.01 for s in samples), "Missing CTA window start"
    assert any(abs(s - 27.0) < 0.01 for s in samples), "Missing CTA window midpoint"


def test_qa_sampling_edge_cases():
    """Verify short and zero duration handling."""
    assert compute_sample_times(0.0) == [0.0]
    short_samples = compute_sample_times(2.0, step=0.5)
    assert min(short_samples) == 0.0
    assert max(short_samples) <= 2.0
    assert len(short_samples) >= 4
