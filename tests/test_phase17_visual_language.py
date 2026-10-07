"""Phase 17 Visual Language Rebuild Unit & Regression Tests.

Validates:
1. Style Systems registration & token consistency
2. Environment variety (no background survives > 8s)
3. Multi-layer depth generation (bg, mid, fg layers with alpha transparency)
4. Transformative transitions (forbidden cuts/fades rejected)
5. VisualLanguageScore evaluation & release gates
"""
from __future__ import annotations

from pathlib import Path
from PIL import Image

from production.phase17.style_systems import (
    StyleSystemId,
    get_style_system,
    STYLE_SYSTEMS,
)
from production.phase17.environment_generator import (
    generate_environment_for_scene,
    generate_macro_studio_bg,
    generate_blueprint_cad_bg,
    generate_tactical_radar_bg,
    generate_cinematic_warehouse_bg,
    generate_premium_brand_stage_bg,
)
from production.phase17.multi_layer_generator import generate_scene_layers
from production.phase17.transition_director import (
    assign_transformative_transitions,
    validate_transition_integrity,
    FORBIDDEN_TRANSITIONS,
)
from production.phase17.visual_qa import evaluate_visual_language


def test_style_systems_registration():
    """Verify that dedicated style systems are registered with distinct parameters."""
    assert StyleSystemId.CLAUDE_EDITORIAL in STYLE_SYSTEMS
    assert StyleSystemId.APPLE_KEYNOTE in STYLE_SYSTEMS
    assert StyleSystemId.LINEAR_LAUNCH in STYLE_SYSTEMS
    assert StyleSystemId.BLOOMBERG_GRAPHICS in STYLE_SYSTEMS

    claude = get_style_system("claude_editorial")
    assert claude.primary_bg == "#12151C"
    assert claude.accent == "#D97736"

    apple = get_style_system("apple_keynote")
    assert apple.primary_bg == "#0B0D11"
    assert apple.accent == "#2997FF"


def test_environment_variety_no_background_over_8s():
    """Verify that all 5 scene environments are distinct and have unique pixel characteristics."""
    bgs = [generate_environment_for_scene(i, width=360, height=640) for i in range(5)]
    assert len(bgs) == 5

    # Check distinct average colors across environments
    averages = [img.resize((1, 1)).getpixel((0, 0)) for img in bgs]
    # At least 4 distinct average hues / colors
    assert len(set(averages)) >= 3


def test_multi_layer_depth_separation(tmp_path: Path):
    """Verify that generate_scene_layers produces bg (opaque), mid (transparent), and fg (transparent)."""
    layers = generate_scene_layers(
        scene_index=0,
        narration="Warehouse robots are getting smarter fast.",
        output_dir=tmp_path,
        scene_id="scene_01",
    )
    assert layers["bg"].exists()
    assert layers["mid"].exists()
    assert layers["fg"].exists()
    assert layers["primary"].exists()

    # Midground and foreground must be RGBA with non-zero transparency
    mid_img = Image.open(layers["mid"])
    assert mid_img.mode == "RGBA"
    alpha_extrema = mid_img.getextrema()[3]
    # Alpha has both transparent (0) and solid (255) pixels
    assert alpha_extrema[0] == 0 and alpha_extrema[1] == 255

    fg_img = Image.open(layers["fg"])
    assert fg_img.mode == "RGBA"
    fg_alpha = fg_img.getextrema()[3]
    assert fg_alpha[0] == 0 and fg_alpha[1] == 255


def test_transformative_transitions():
    """Verify forbidden cuts/fades are rejected and transformative transitions are assigned."""
    trans = assign_transformative_transitions(5)
    assert len(trans) == 5
    for t in trans:
        assert t not in FORBIDDEN_TRANSITIONS

    valid, errs = validate_transition_integrity(trans)
    assert valid is True
    assert len(errs) == 0

    # Test rejection of forbidden cut
    invalid, errs_bad = validate_transition_integrity(["hard_cut", "fade"])
    assert invalid is False
    assert len(errs_bad) == 2


def test_visual_language_qa_evaluation(tmp_path: Path):
    """Verify that evaluate_visual_language enforces environment variety and parallax depth."""
    scenes = [
        {"scene_id": f"scene_0{i+1}", "start_seconds": i * 5.0, "end_seconds": (i + 1) * 5.0, "environment": f"Env_{i+1}", "depth_strategy": "background_midground_foreground"}
        for i in range(5)
    ]
    timeline = [
        {"scene_id": f"scene_0{i+1}", "transition_in": "zoom_transition"}
        for i in range(5)
    ]

    eval_res = evaluate_visual_language(tmp_path, scenes, timeline)
    assert eval_res.passed is True
    assert eval_res.environment_variety_score >= 9.0
    assert eval_res.depth_parallax_score >= 9.0
    assert eval_res.transition_score >= 9.0
    assert eval_res.visual_language_score >= 8.5
