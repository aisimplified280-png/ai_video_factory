"""Tests for Variety Governor rules and diversity scoring."""
import pytest
from stages.scene_plan.variety_governor import VarietyGovernor


@pytest.fixture
def diverse_scenes():
    return [
        {
            "id": "scene_01",
            "type": "animation",
            "visual_technique": "diagram_reveal",
            "composition_intent": "wide isometric landscape",
            "camera_intent": "reveal_space",
            "motion_intent": "emerge",
        },
        {
            "id": "scene_02",
            "type": "diagram",
            "visual_technique": "analogy_visualization",
            "composition_intent": "split-screen comparison",
            "camera_intent": "approach_subject",
            "motion_intent": "assemble",
        },
        {
            "id": "scene_03",
            "type": "broll",
            "visual_technique": "evidence_wall",
            "composition_intent": "macro focal detail",
            "camera_intent": "shift_focus",
            "motion_intent": "flow",
        },
        {
            "id": "scene_04",
            "type": "text_card",
            "visual_technique": "kinetic_typography",
            "composition_intent": "centered brand focus",
            "camera_intent": "expand_scale",
            "motion_intent": "pulse",
        },
    ]


def test_governor_approves_diverse_scenes(diverse_scenes):
    governor = VarietyGovernor()
    report = governor.evaluate(diverse_scenes)
    assert report.is_valid
    assert report.variety_score >= 70.0
    assert len(report.findings) == 0


def test_governor_rejects_3_consecutive_identical_scene_types(diverse_scenes):
    # Set scenes 0, 1, 2 to "animation"
    for s in diverse_scenes[:3]:
        s["type"] = "animation"

    governor = VarietyGovernor()
    report = governor.evaluate(diverse_scenes)
    assert not report.is_valid
    codes = [f.code for f in report.findings]
    assert "CONSECUTIVE_IDENTICAL_SCENE_TYPES" in codes


def test_governor_rejects_3_consecutive_identical_techniques(diverse_scenes):
    for s in diverse_scenes[:3]:
        s["visual_technique"] = "diagram_reveal"

    governor = VarietyGovernor()
    report = governor.evaluate(diverse_scenes)
    assert not report.is_valid
    codes = [f.code for f in report.findings]
    assert "CONSECUTIVE_IDENTICAL_TECHNIQUES" in codes


def test_governor_rejects_3_consecutive_identical_compositions(diverse_scenes):
    for s in diverse_scenes[:3]:
        s["composition_intent"] = "centered layout"

    governor = VarietyGovernor()
    report = governor.evaluate(diverse_scenes)
    assert not report.is_valid
    codes = [f.code for f in report.findings]
    assert "CONSECUTIVE_IDENTICAL_COMPOSITIONS" in codes


def test_governor_rejects_insufficient_distinct_techniques():
    scenes = [
        {"id": f"scene_{i}", "type": "animation" if i % 2 == 0 else "diagram",
         "visual_technique": "diagram_reveal", "composition_intent": f"comp_{i}"}
        for i in range(5)
    ]
    governor = VarietyGovernor(min_distinct_techniques=3)
    report = governor.evaluate(scenes)
    assert not report.is_valid
    codes = [f.code for f in report.findings]
    assert "INSUFFICIENT_DISTINCT_TECHNIQUES" in codes


def test_governor_enforces_art_direction_anti_patterns(diverse_scenes):
    art_direction = {
        "anti_patterns": [
            "no floating cards every scene",
            "no text-only explanation without visual anchor",
        ]
    }
    # Violate floating cards: add multiple floating cards
    diverse_scenes[0]["composition_intent"] = "floating card with metrics"
    diverse_scenes[1]["composition_intent"] = "floating card with charts"

    governor = VarietyGovernor()
    report = governor.evaluate(diverse_scenes, art_direction=art_direction)
    assert not report.is_valid
    codes = [f.code for f in report.findings]
    assert "ANTI_PATTERN_VIOLATION_CARDS" in codes
