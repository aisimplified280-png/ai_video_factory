"""Unit tests for stages/assets/asset_selector.py."""
import pytest
from stages.assets.asset_selector import AssetSelector


@pytest.fixture
def selector():
    return AssetSelector()


@pytest.fixture
def sample_art_direction():
    return {
        "design_read": "High-contrast technical schematic with industrial physical metaphors.",
        "visual_metaphor": "industrial transformer overloaded under computational demand",
        "palette_discipline": {
            "primary": "#0A0D14",
            "accent_1": "#00FF88",
            "mood": "industrial technical",
        },
        "anti_patterns": ["no floating cards", "no generic 3D neon brain"],
    }


def test_select_strategy_for_diagram_scene(selector, sample_art_direction):
    scene = {
        "scene_id": "scene_02",
        "narrative_role": "mechanism",
        "visual_technique": "system_assembly",
        "type": "diagram",
        "subject": "Neural routing crossbar",
        "subject_action": "Interlocking request routing nodes",
        "visual_purpose": "Explain multi-agent task execution mechanism",
        "start_seconds": 5.0,
        "end_seconds": 12.0,
    }
    item = selector.select_asset_strategy(
        scene=scene,
        scene_idx=1,
        total_scenes=5,
        art_direction=sample_art_direction,
        production_id="proj_test_01",
    )

    assert item.asset_id == "ast_scene_02_primary"
    assert item.type == "diagram"
    assert item.source == "native"
    assert item.provider == "native_diagram"
    assert "programmatic_svg" in item.fallback_chain
    assert item.diagram_spec is not None
    assert item.diagram_spec["subject"] == "Neural routing crossbar"


def test_select_strategy_for_cta_scene(selector, sample_art_direction):
    scene = {
        "scene_id": "scene_05",
        "narrative_role": "cta",
        "visual_technique": "kinetic_typography",
        "type": "text_card",
        "subject": "AI Simplified Lab Brand Identity",
        "subject_action": "Pulsing subscription CTA",
        "visual_purpose": "Convert attention into subscription.",
        "start_seconds": 40.0,
        "end_seconds": 45.0,
    }
    item = selector.select_asset_strategy(
        scene=scene,
        scene_idx=4,
        total_scenes=5,
        art_direction=sample_art_direction,
        production_id="proj_test_01",
    )

    assert item.type == "logo"
    assert item.source == "local_library"
    assert "local_library_brand" in item.fallback_chain


def test_select_strategy_for_cinematic_broll_scene(selector, sample_art_direction):
    scene = {
        "scene_id": "scene_01",
        "narrative_role": "hook",
        "visual_technique": "cinematic_broll",
        "type": "broll",
        "subject": "Massive industrial transformer",
        "subject_action": "Overloading with glowing copper coils and spiking gauges",
        "visual_purpose": "Establish physical scale of compute demand",
        "start_seconds": 0.0,
        "end_seconds": 6.0,
    }
    item = selector.select_asset_strategy(
        scene=scene,
        scene_idx=0,
        total_scenes=5,
        art_direction=sample_art_direction,
        production_id="proj_test_01",
    )

    assert item.type in ("video", "image")
    assert item.source == "generated"
    assert item.fallback_chain[0] in ("primary_video_generator", "primary_image_generator")
    assert "explicit_blocker" in item.fallback_chain


def test_purpose_minimum_length_enforced(selector, sample_art_direction):
    scene = {
        "scene_id": "scene_03",
        "narrative_role": "evidence",
        "visual_technique": "evidence_wall",
        "type": "image",
        "subject": "Server cluster racks",
        "visual_purpose": "img",  # Too short
        "start_seconds": 10.0,
        "end_seconds": 15.0,
    }
    item = selector.select_asset_strategy(
        scene=scene,
        scene_idx=2,
        total_scenes=5,
        art_direction=sample_art_direction,
        production_id="proj_test_01",
    )
    assert len(item.purpose) >= 10
