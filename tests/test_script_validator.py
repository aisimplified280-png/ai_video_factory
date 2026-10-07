"""Tests for script validator rules (hooks, CTA, visual intent, entity leaks)."""
import pytest
from stages.script.script_validator import ScriptValidator


@pytest.fixture
def valid_script_payload():
    return {
        "title": "Why AI Models Need More Compute",
        "hook": "Every time an AI model gets twice as smart, the compute needed does not double—it multiplies by ten.",
        "target_duration_seconds": 45.0,
        "sections": [
            {
                "id": "sec_01",
                "narrative_role": "hook",
                "spoken_text": "Every time an AI model gets twice as smart, the compute needed does not double—it multiplies by ten.",
                "estimated_start": 0.0,
                "estimated_end": 6.5,
                "duration": 6.5,
                "visual_intent": "Massive scale comparison showing an exponential power curve rising into the clouds.",
                "primary_intent": "reveal",
                "secondary_intents": ["show_scale"],
                "primary_subject": "Compute scaling",
                "entities": ["AI models", "power curve"],
                "emphasis_words": ["MULTIPACT"],
            },
            {
                "id": "sec_02",
                "narrative_role": "mechanism",
                "spoken_text": "Training isn't just memorizing data. It's computing trillions of matrix multiplications across clustered GPUs.",
                "estimated_start": 6.5,
                "estimated_end": 18.0,
                "duration": 11.5,
                "visual_intent": "Cluster floor isometric view as matrices cascade across parallel server blades.",
                "primary_intent": "show_process",
                "secondary_intents": [],
                "primary_subject": "Matrix operations",
                "entities": ["GPU clusters", "matrix multiplications"],
                "emphasis_words": ["TRILLIONS"],
            },
            {
                "id": "sec_03",
                "narrative_role": "evidence",
                "spoken_text": "Frontier data centers now draw gigawatts of power, rivaling the electrical demand of medium-sized cities.",
                "estimated_start": 18.0,
                "estimated_end": 30.0,
                "duration": 12.0,
                "visual_intent": "Telemetry map comparing regional power consumption against a single hyperscale AI facility.",
                "primary_intent": "show_evidence",
                "secondary_intents": ["show_scale"],
                "primary_subject": "Data center power",
                "entities": ["Data centers", "power grid"],
                "emphasis_words": ["GIGAWATTS"],
            },
            {
                "id": "sec_04",
                "narrative_role": "payoff",
                "spoken_text": "The bottleneck isn't algorithms anymore; it's the physical energy to run the machine.",
                "estimated_start": 30.0,
                "estimated_end": 40.0,
                "duration": 10.0,
                "visual_intent": "Macro view of transformers under load with thermal imaging overlay.",
                "primary_intent": "explain",
                "secondary_intents": [],
                "primary_subject": "Energy bottleneck",
                "entities": ["Physical bottleneck", "transformers"],
                "emphasis_words": ["ENERGY"],
            },
            {
                "id": "sec_05",
                "narrative_role": "cta",
                "spoken_text": "Subscribe to AI Simplified Lab for more breakdowns like this.",
                "estimated_start": 40.0,
                "estimated_end": 44.5,
                "duration": 4.5,
                "visual_intent": "Brand signature sequence with dynamic subscribe button interaction.",
                "primary_intent": "conclude",
                "secondary_intents": [],
                "primary_subject": "Channel identity",
                "entities": ["AI Simplified Lab"],
                "emphasis_words": ["SUBSCRIBE"],
            },
        ],
    }


def test_validator_approves_valid_script(valid_script_payload):
    validator = ScriptValidator()
    report = validator.validate(valid_script_payload)
    assert report.is_valid
    assert report.status == "approved"
    assert len(report.findings) == 0


@pytest.mark.parametrize("generic_hook", [
    "Today we're going to discuss AI compute scaling.",
    "Artificial intelligence is changing how we compute things.",
    "In this video we will explore data centers.",
    "Let's take a look at GPUs.",
])
def test_validator_rejects_generic_hook(valid_script_payload, generic_hook):
    valid_script_payload["sections"][0]["spoken_text"] = generic_hook
    valid_script_payload["hook"] = generic_hook
    validator = ScriptValidator()
    report = validator.validate(valid_script_payload)
    assert not report.is_valid
    codes = [f.code for f in report.findings]
    assert "GENERIC_HOOK_REJECTED" in codes


def test_validator_rejects_missing_cta(valid_script_payload):
    valid_script_payload["sections"] = valid_script_payload["sections"][:-1]
    validator = ScriptValidator()
    report = validator.validate(valid_script_payload)
    assert not report.is_valid
    codes = [f.code for f in report.findings]
    assert "MISSING_CTA_SECTION" in codes


def test_validator_rejects_cta_not_final(valid_script_payload):
    cta = valid_script_payload["sections"].pop()
    valid_script_payload["sections"].insert(1, cta)
    validator = ScriptValidator()
    report = validator.validate(valid_script_payload)
    assert not report.is_valid
    codes = [f.code for f in report.findings]
    assert "CTA_NOT_FINAL_SECTION" in codes


def test_validator_rejects_weak_visual_intent(valid_script_payload):
    valid_script_payload["sections"][0]["visual_intent"] = "Headline and supporting text on screen"
    validator = ScriptValidator()
    report = validator.validate(valid_script_payload)
    assert not report.is_valid
    codes = [f.code for f in report.findings]
    assert "WEAK_VISUAL_INTENT" in codes


def test_validator_rejects_emphasis_in_entities(valid_script_payload):
    valid_script_payload["sections"][0]["emphasis_words"] = ["MASSIVE"]
    valid_script_payload["sections"][0]["entities"] = ["massive", "AI models"]
    validator = ScriptValidator()
    report = validator.validate(valid_script_payload)
    assert not report.is_valid
    codes = [f.code for f in report.findings]
    assert "EMPHASIS_AS_ENTITY_LEAK" in codes
