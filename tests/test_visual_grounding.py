"""Test suite for Visual Grounding, Scene Diversity, and Visual QA.

Validates:
- Concrete physical objects, locations, and actions are extracted (no cliché glowing blue holograms).
- Topic "GPT-6 Astra controls robots" yields robot arm, warehouse/factory, physical actuators.
- Scene concepts maintain >= 70% uniqueness ratio across multi-scene videos.
- Every scene concept contains structured scene breakdown with location, camera, lighting, action, emotion.
- Visual QA rejects cartoons, flat artifacts, and invalid resolutions while accepting cinematic documentary standards.
"""
from __future__ import annotations

from PIL import Image
import pytest

from production.phase10.models import ClaimRecord, ClaimStatus, SourceRecord
from production.phase10.visual_extractor import extract_visual_facts
from production.phase9.planner import generate_plan
from production.phase9.visual_qa import sanitize_cinematic_prompt, validate_image_quality


def test_visual_grounding_for_robotics_topic():
    sources = [
        SourceRecord(
            source_id="src_001",
            title="OpenAI demonstrates GPT-6 Astra controlling robot arm in factory warehouse",
            publisher="techcrunch.com",
            url="https://techcrunch.com/gpt-6-astra-robot",
            retrieved_at="2026-10-07T00:00:00Z",
            source_type="news",
            snippet="The robot arm was sorting packages using a camera rig and multi-axis manipulator.",
            tier=2,
        )
    ]
    claims = [
        ClaimRecord(
            claim_id="c_01",
            claim="GPT-6 Astra controls robots in industrial manufacturing",
            status=ClaimStatus.CONFIRMED,
            confidence=0.9,
            source_ids=["src_001"],
        )
    ]

    vf = extract_visual_facts("GPT-6 Astra controls robots", sources, claims)

    # Must extract physical hardware and concrete environments
    combined_objects = " ".join(vf.objects).lower()
    combined_locations = " ".join(vf.locations).lower()

    assert any(term in combined_objects for term in ["robot arm", "actuator", "manipulator", "camera rig"])
    assert any(term in combined_locations for term in ["robotics lab", "warehouse", "plant", "facility"])

    # Must reject cliché holographic tropes
    prompt_seed = vf.visual_prompt_seed.lower()
    assert "blue hologram" not in prompt_seed
    assert "generic ai interface" not in prompt_seed
    assert "matrix" not in prompt_seed
    assert "Cinematic documentary" in vf.visual_prompt_seed


def test_scene_diversity_target_met():
    script_data = {
        "data": {
            "sections": [
                {"section_id": "sec_01", "spoken_text": "First we examine the robotics plant.", "emphasis_words": []},
                {"section_id": "sec_02", "spoken_text": "Then we move into the warehouse operations.", "emphasis_words": []},
                {"section_id": "sec_03", "spoken_text": "Next we inspect the cleanroom wafer fabrication.", "emphasis_words": []},
                {"section_id": "sec_04", "spoken_text": "Finally telemetry data flows to the control room.", "emphasis_words": []},
            ]
        }
    }
    prod_state = {"research_data": {}}
    plan = generate_plan(script_data, prod_state)

    metrics = plan.get("diversity_metrics", {})
    assert metrics.get("target_met") is True
    assert metrics.get("scene_diversity_ratio", 0) >= 0.70

    # Ensure unique locations across scenes
    environments = [s["environment"] for s in plan["scene_concepts"]]
    assert len(set(environments)) >= 3


def test_structured_scene_breakdown_present_on_all_scenes():
    script_data = {
        "data": {
            "sections": [
                {"section_id": "sec_01", "spoken_text": "Robotics automation test.", "emphasis_words": []},
            ]
        }
    }
    plan = generate_plan(script_data, {})
    concept = plan["scene_concepts"][0]
    assert "scene_breakdown" in concept
    breakdown = concept["scene_breakdown"]
    assert "location" in breakdown
    assert "main_subject" in breakdown
    assert "camera" in breakdown
    assert "lighting" in breakdown
    assert "action" in breakdown
    assert "emotion" in breakdown


def test_visual_qa_quality_gate(tmp_path):
    from PIL import ImageDraw
    valid_img = Image.new("RGB", (1080, 1920), (30, 45, 60))
    d = ImageDraw.Draw(valid_img)
    for y in range(0, 1920, 10):
        d.line([(0, y), (1080, y)], fill=(int(y / 1920 * 200), 50, 120))
    is_valid, msg = validate_image_quality(valid_img, "cinematic documentary")
    assert is_valid is True

    # 2. Reject flat/solid color image
    flat_img = Image.new("RGB", (1080, 1920), (10, 10, 10))
    is_valid, msg = validate_image_quality(flat_img, "cinematic documentary")
    assert is_valid is False
    assert "detail" in msg.lower() or "stddev" in msg.lower()

    # 3. Reject wrong aspect ratio (horizontal)
    horizontal_img = Image.new("RGB", (1920, 1080), (100, 100, 100))
    is_valid, msg = validate_image_quality(horizontal_img, "cinematic documentary")
    assert is_valid is False
    assert "aspect ratio" in msg.lower()

    # 4. Reject anime / cartoon prompts
    is_valid, msg = validate_image_quality(valid_img, prompt="anime girl robot")
    assert is_valid is False
    assert "anime" in msg.lower()


def test_sanitize_cinematic_prompt():
    raw_prompt = "robot arm sorting parts"
    sanitized = sanitize_cinematic_prompt(raw_prompt)
    assert "cinematic documentary" in sanitized
    assert "no anime" in sanitized
    assert "no cartoon" in sanitized
