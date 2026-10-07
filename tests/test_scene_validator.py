"""Tests for scene plan validator rules."""
import pytest
from stages.scene_plan.scene_validator import SceneValidator


@pytest.fixture
def valid_scene_plan_payload():
    return {
        "total_duration_seconds": 45.0,
        "variety_score": 85.0,
        "scenes": [
            {
                "id": "scene_01",
                "scene_id": "scene_01",
                "type": "animation",
                "script_section_id": "sec_01",
                "start_seconds": 0.0,
                "end_seconds": 6.5,
                "narrative_role": "hook",
                "information_role": "reveal",
                "viewer_understanding": "Viewer grasps the physical scale gap between human software and exponential neural network infrastructure.",
                "visual_purpose": "establish scale",
                "visual_metaphor": "server rooms behaving like an industrial power grid",
                "subject": "Compute infrastructure",
                "subject_action": "Power grid surge illuminating sprawling server arrays",
                "environment": "Hyperscale data hall",
                "composition_intent": "wide isometric landscape",
                "camera_intent": "reveal_space",
                "motion_intent": "emerge",
                "visual_technique": "scale_transition",
                "shots": [
                    {"shot_id": "s1_shot_01", "start": 0.0, "end": 3.25, "purpose": "Establish scale", "focus_subject": "array", "visual_change": "reveal", "camera_intent": "reveal_space", "motion_intent": "emerge", "transition": "cut"},
                    {"shot_id": "s1_shot_02", "start": 3.25, "end": 6.5, "purpose": "Surge detail", "focus_subject": "grid", "visual_change": "illumination", "camera_intent": "approach_subject", "motion_intent": "assemble", "transition": "cut"},
                ],
                "required_assets": [{"asset_type": "generated_video", "purpose": "show server array", "visual_role": "primary"}],
            },
            {
                "id": "scene_02",
                "scene_id": "scene_02",
                "type": "diagram",
                "script_section_id": "sec_02",
                "start_seconds": 6.5,
                "end_seconds": 18.0,
                "narrative_role": "mechanism",
                "information_role": "show_process",
                "viewer_understanding": "Viewer visualizes how tensor operations parallelize across millions of streaming multiprocessors.",
                "visual_purpose": "show mechanism",
                "visual_metaphor": "server rooms behaving like an industrial power grid",
                "subject": "Matrix multiplication fabric",
                "subject_action": "Tensors flowing through interconnected silicon routing channels",
                "environment": "Microchip silicon architecture",
                "composition_intent": "split-screen dynamic",
                "camera_intent": "approach_subject",
                "motion_intent": "assemble",
                "visual_technique": "diagram_reveal",
                "shots": [
                    {"shot_id": "s2_shot_01", "start": 0.0, "end": 5.75, "purpose": "Flow initiation", "focus_subject": "tensors", "visual_change": "flow", "camera_intent": "approach_subject", "motion_intent": "assemble", "transition": "cut"},
                    {"shot_id": "s2_shot_02", "start": 5.75, "end": 11.5, "purpose": "Routing resolve", "focus_subject": "silicon", "visual_change": "routing", "camera_intent": "shift_focus", "motion_intent": "flow", "transition": "cut"},
                ],
                "required_assets": [{"asset_type": "native_diagram", "purpose": "tensor dataflow", "visual_role": "primary"}],
            },
            {
                "id": "scene_03",
                "scene_id": "scene_03",
                "type": "broll",
                "script_section_id": "sec_03",
                "start_seconds": 18.0,
                "end_seconds": 30.0,
                "narrative_role": "evidence",
                "information_role": "show_evidence",
                "viewer_understanding": "Viewer compares national electrical substation capacity directly to modern AI cluster power consumption.",
                "visual_purpose": "provide evidence",
                "visual_metaphor": "server rooms behaving like an industrial power grid",
                "subject": "Regional electrical grid telemetry",
                "subject_action": "Thermal telemetry maps overlaying high-voltage transmission lines",
                "environment": "Regional grid command map",
                "composition_intent": "macro focal detail",
                "camera_intent": "shift_focus",
                "motion_intent": "flow",
                "visual_technique": "evidence_wall",
                "shots": [
                    {"shot_id": "s3_shot_01", "start": 0.0, "end": 6.0, "purpose": "Map reveal", "focus_subject": "telemetry", "visual_change": "overlay", "camera_intent": "shift_focus", "motion_intent": "flow", "transition": "cut"},
                    {"shot_id": "s3_shot_02", "start": 6.0, "end": 12.0, "purpose": "Capacity contrast", "focus_subject": "lines", "visual_change": "contrast", "camera_intent": "expand_scale", "motion_intent": "trace", "transition": "cut"},
                ],
                "required_assets": [{"asset_type": "generated_video", "purpose": "power telemetry map", "visual_role": "primary"}],
            },
            {
                "id": "scene_04",
                "scene_id": "scene_04",
                "type": "text_card",
                "script_section_id": "sec_04",
                "start_seconds": 30.0,
                "end_seconds": 45.0,
                "narrative_role": "cta",
                "information_role": "conclude",
                "viewer_understanding": "Viewer knows how to continue following the channel and subscribe.",
                "visual_purpose": "Convert attention into subscription.",
                "visual_metaphor": "server rooms behaving like an industrial power grid",
                "subject": "AI Simplified Lab Brand Identity",
                "subject_action": "Kinetic subscription trigger and telemetry logo assembly",
                "environment": "Clean brand atmosphere",
                "composition_intent": "centered brand focus",
                "camera_intent": "expand_scale",
                "motion_intent": "pulse",
                "visual_technique": "kinetic_typography",
                "shots": [
                    {"shot_id": "s4_shot_01", "start": 0.0, "end": 15.0, "purpose": "Subscribe cue", "focus_subject": "brand", "visual_change": "assembly", "camera_intent": "expand_scale", "motion_intent": "pulse", "transition": "cut"},
                ],
                "required_assets": [{"asset_type": "brand_asset", "purpose": "channel identity", "visual_role": "primary"}],
            },
        ],
    }


def test_validator_approves_valid_scene_plan(valid_scene_plan_payload):
    script_data = {"sections": [{"section_id": "sec_01"}, {"section_id": "sec_02"}, {"section_id": "sec_03"}, {"section_id": "sec_04"}]}
    validator = SceneValidator()
    report = validator.validate(valid_scene_plan_payload, script_data=script_data)
    assert report.is_valid
    assert report.status == "approved"


@pytest.mark.parametrize("generic_metaphor", [
    "modern ai graphics",
    "futuristic technology",
    "dynamic visuals",
    "technology visualization",
])
def test_validator_rejects_generic_visual_metaphor(valid_scene_plan_payload, generic_metaphor):
    valid_scene_plan_payload["scenes"][0]["visual_metaphor"] = generic_metaphor
    validator = SceneValidator()
    report = validator.validate(valid_scene_plan_payload)
    assert not report.is_valid
    codes = [f.code for f in report.findings]
    assert "GENERIC_VISUAL_METAPHOR" in codes


def test_validator_rejects_generic_viewer_understanding(valid_scene_plan_payload):
    valid_scene_plan_payload["scenes"][0]["viewer_understanding"] = "Viewer sees AI visualization."
    validator = SceneValidator()
    report = validator.validate(valid_scene_plan_payload)
    assert not report.is_valid
    codes = [f.code for f in report.findings]
    assert "GENERIC_VIEWER_UNDERSTANDING" in codes


def test_validator_rejects_cta_not_final(valid_scene_plan_payload):
    cta_scene = valid_scene_plan_payload["scenes"].pop()
    valid_scene_plan_payload["scenes"].insert(1, cta_scene)
    validator = SceneValidator()
    report = validator.validate(valid_scene_plan_payload)
    assert not report.is_valid
    codes = [f.code for f in report.findings]
    assert "CTA_NOT_FINAL_SCENE" in codes


def test_validator_detects_uncovered_script_section(valid_scene_plan_payload):
    script_data = {
        "sections": [
            {"section_id": "sec_01"},
            {"section_id": "sec_02"},
            {"section_id": "sec_03"},
            {"section_id": "sec_04"},
            {"section_id": "sec_orphan"},
        ]
    }
    validator = SceneValidator()
    report = validator.validate(valid_scene_plan_payload, script_data=script_data)
    assert not report.is_valid
    codes = [f.code for f in report.findings]
    assert "UNCOVERED_SCRIPT_SECTIONS" in codes


def test_validator_rejects_shot_timing_gaps(valid_scene_plan_payload):
    # Introduce gap into scene 1 shots: shot 1 ends at 2.0, shot 2 starts at 3.0
    valid_scene_plan_payload["scenes"][0]["shots"][0]["end"] = 2.0
    valid_scene_plan_payload["scenes"][0]["shots"][1]["start"] = 3.0
    validator = SceneValidator()
    report = validator.validate(valid_scene_plan_payload)
    assert not report.is_valid
    codes = [f.code for f in report.findings]
    assert "INVALID_SHOT_COVERAGE" in codes
