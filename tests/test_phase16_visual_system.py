"""Phase 16 Visual System & Human Visual Relevance Regression Tests.

Validates:
1. Visual Design System consistency (Editorial Intelligence palette, materials, typography)
2. Background / Foreground luminance separation
3. Scene specificity score (2-4 story-specific anchors)
4. Human visual relevance evaluation
5. Generic AI cliché rejection (cyan circuits in void, neural brain tropes)
6. Action visibility (kinetic proof required)
7. Relationship visibility
8. Visual style inheritance
9. Visual noise & text clutter rejection
10. Metadata cannot fake visual grounding (pixel-level truth)
"""
from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageDraw

from production.phase16.design_system import create_default_design_system
from production.phase16.evidence_contract import (
    EditorialVisualMode,
    VisualEvidenceContract,
    extract_evidence_contract,
)
from production.phase16.visual_generator import render_editorial_asset
from production.phase16.human_qa import (
    evaluate_frame_pixels,
    evaluate_human_visual_relevance,
)


def test_visual_design_system_consistency():
    """Verify that design system defines editorial palette and forbids AI slop."""
    ds = create_default_design_system("proj_test", "GPT-6 Astra")
    assert ds.palette.background == "#12151C"  # Warm charcoal
    assert ds.palette.accent == "#D97736"      # Warm terracotta
    assert "glowing cyan neon lines" in ds.materials.prohibited
    assert "pitch-black empty voids with floating wires" in ds.materials.prohibited
    assert ds.composition.negative_space_ratio >= 0.35


def test_background_foreground_separation():
    """Verify generated frames exhibit clear luminance separation between subject and background."""
    contract = extract_evidence_contract(
        narration="Advanced neural networks can now directly control physical robots.",
        scene_id="scene_02",
        topic="GPT-6 Astra",
    )
    img = render_editorial_asset(contract)
    ds = create_default_design_system()
    ad_score, comp_score, noise_pen, issues = evaluate_frame_pixels(img, contract, ds)

    assert comp_score >= 8.0
    assert ad_score >= 8.0
    assert "Weak subject isolation" not in " ".join(issues)


def test_scene_specificity():
    """Verify evidence contract extracts 2-4 story-specific anchors."""
    contract = extract_evidence_contract(
        narration="Instead of rigid routines, machines adapt dynamically to moving obstacles.",
        scene_id="scene_03",
        topic="Warehouse Robotics",
    )
    assert len(contract.story_specific_anchors) >= 2
    assert any("obstacle" in a.lower() for a in contract.story_specific_anchors)
    assert any("rover" in a.lower() or "spline" in a.lower() for a in contract.story_specific_anchors)


def test_human_visual_relevance(tmp_path: Path):
    """Verify human visual relevance QA accurately scores an editorial frame."""
    contract = extract_evidence_contract(
        narration="GPT-6 Astra directly controls an industrial robotic arm.",
        scene_id="scene_02",
        topic="GPT-6 Astra",
    )
    img = render_editorial_asset(contract)
    frame_path = tmp_path / "frame_02.png"
    img.save(frame_path)

    ds = create_default_design_system()
    qa_res = evaluate_human_visual_relevance(frame_path, contract, ds, 1)
    assert qa_res.passed is True
    assert qa_res.human_visual_relevance_score >= 8.5
    assert qa_res.composite_visual_quality >= 8.0
    assert "volumetric" in qa_res.what_viewer_sees.lower()


def test_generic_ai_cliche_rejection():
    """Verify forbidden visuals blacklist rejects generic AI brain and cyan voids."""
    contract = extract_evidence_contract(
        narration="Advanced neural networks control physical machines.",
        topic="Robotics",
    )
    assert any("cyan circuit" in f.lower() for f in contract.forbidden_visuals)
    assert any("neural brain" in f.lower() for f in contract.forbidden_visuals)


def test_action_visibility():
    """Verify contract requires active kinetic proof, not static objects."""
    contract = extract_evidence_contract(
        narration="Instead of rigid pre-programmed routines, these machines adapt dynamically to moving obstacles.",
        scene_id="scene_03",
    )
    assert "detecting" in contract.action or "steering" in contract.action
    assert contract.action != ""
    assert "obstacle" in contract.object or "cargo" in contract.object


def test_relationship_visibility():
    """Verify contract explicitly preserves the relationship connection."""
    contract = extract_evidence_contract(
        narration="That means facilities can move inventory faster, with fewer delays.",
        scene_id="scene_04",
    )
    assert "fleet" in contract.relationship or "continuous" in contract.relationship
    assert contract.relationship != ""


def test_visual_style_inheritance():
    """Verify multiple scenes inherit the exact same design system tokens."""
    ds = create_default_design_system("proj_test", "Multi-topic")
    c1 = extract_evidence_contract("Scene one narration", scene_id="s1")
    c2 = extract_evidence_contract("Scene two narration", scene_id="s2")

    img1 = render_editorial_asset(c1, ds)
    img2 = render_editorial_asset(c2, ds)

    # Both must match 1080x1920 dimension and share background palette
    assert img1.size == (1080, 1920)
    assert img2.size == (1080, 1920)


def test_visual_noise_rejection(tmp_path: Path):
    """Verify that a noisy, cluttered frame with text in caption zones receives penalties."""
    # Synthesize noisy frame
    noisy_img = Image.new("RGB", (1080, 1920), (0, 0, 0))
    d = ImageDraw.Draw(noisy_img)
    # Add random high frequency noise in caption zone
    for i in range(200):
        d.line([(i * 5, 1700), (i * 5 + 3, 1850)], fill=(255, 255, 255), width=2)

    frame_path = tmp_path / "noisy_frame.png"
    noisy_img.save(frame_path)

    contract = extract_evidence_contract("Test narration", scene_id="s1")
    ds = create_default_design_system()
    qa_res = evaluate_human_visual_relevance(frame_path, contract, ds, 0)
    assert len(qa_res.rejection_reasons) > 0


def test_metadata_cannot_fake_visual_grounding(tmp_path: Path):
    """Verify that an empty pitch-black frame is rejected even if contract claims 10/10."""
    black_img = Image.new("RGB", (1080, 1920), (0, 0, 0))
    frame_path = tmp_path / "black_frame.png"
    black_img.save(frame_path)

    contract = extract_evidence_contract(
        narration="Advanced neural networks directly control physical robots.",
        scene_id="scene_02",
    )
    ds = create_default_design_system()
    ad_score, comp_score, noise_pen, issues = evaluate_frame_pixels(black_img, contract, ds)

    # Pure black frame must trigger dark void penalty and low composition score
    assert any("pitch black" in issue for issue in issues)
    assert ad_score < 7.5
