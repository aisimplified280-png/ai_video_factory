"""Tests for script timing engine and duration validation."""
import pytest
from stages.script.timing import (
    count_words,
    estimate_spoken_duration,
    apply_script_timing,
    validate_script_timing,
)


def test_count_words():
    assert count_words("") == 0
    assert count_words("Hello world") == 2
    assert count_words("State-of-the-art AI, compute-heavy!") == 3


def test_estimate_spoken_duration_includes_punctuation_pauses():
    simple = "This is a quick sentence"
    punctuated = "This is a sentence. Wait! What happens next?"
    d_simple = estimate_spoken_duration(simple, speaking_rate_wps=2.5, pause_after=0.0)
    d_punct = estimate_spoken_duration(punctuated, speaking_rate_wps=2.5, pause_after=0.0)
    assert d_punct > d_simple


def test_apply_script_timing_monotonic_and_continuous():
    sections = [
        {"spoken_text": "First beat of the video establishing the primary conflict.", "pause_after": 0.2},
        {"spoken_text": "Second beat revealing the deep technical mechanism.", "pause_after": 0.2},
        {"spoken_text": "Third beat providing empirical evidence and benchmarks.", "pause_after": 0.2},
        {"spoken_text": "Subscribe to AI Simplified Lab for more breakdowns.", "pause_after": 0.3},
    ]

    timed, total_dur, words = apply_script_timing(sections, target_duration=45.0)
    assert len(timed) == 4
    assert total_dur > 0
    assert words > 0

    # Verify monotonic continuity
    for i in range(len(timed) - 1):
        assert timed[i]["estimated_end"] == timed[i + 1]["estimated_start"]
        assert timed[i]["id"] == f"sec_{i+1:02d}"


def test_validate_script_timing_detects_too_short():
    short_sections = [
        {"id": "sec_01", "spoken_text": "Too short.", "estimated_start": 0.0, "estimated_end": 5.0, "duration": 5.0},
    ]
    res = validate_script_timing(short_sections, min_duration=30.0, max_duration=60.0, min_words=50)
    assert res.status == "invalid"
    codes = [f.code for f in res.findings]
    assert "SCRIPT_TOO_SHORT" in codes
    assert "WORD_COUNT_TOO_LOW" in codes


def test_validate_script_timing_detects_too_long():
    long_sections = [
        {"id": f"sec_{i:02d}", "spoken_text": "Lots of narration words here filling up the timeline for testing purposes.",
         "estimated_start": i * 15.0, "estimated_end": (i + 1) * 15.0, "duration": 15.0}
        for i in range(5)
    ]
    res = validate_script_timing(long_sections, min_duration=30.0, max_duration=60.0, min_words=50)
    assert res.status == "invalid"
    codes = [f.code for f in res.findings]
    assert "SCRIPT_TOO_LONG" in codes


def test_validate_script_timing_detects_overlap():
    sections = [
        {"id": "sec_01", "spoken_text": "First section narration.", "estimated_start": 0.0, "estimated_end": 10.0, "duration": 10.0},
        {"id": "sec_02", "spoken_text": "Second section narration.", "estimated_start": 8.0, "estimated_end": 18.0, "duration": 10.0},
    ]
    res = validate_script_timing(sections, min_duration=10.0, max_duration=60.0, min_words=5)
    assert res.status == "invalid"
    codes = [f.code for f in res.findings]
    assert "SECTION_TIMING_OVERLAP" in codes
