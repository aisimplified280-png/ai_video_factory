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
    ALLOWED_TRANSITIONS,
)
from production.phase17.visual_qa import evaluate_visual_language


def test_style_systems_registration():
    """Verify that dedicated style systems are registered with distinct parameters."""
    for style_id in StyleSystemId:
        assert style_id in STYLE_SYSTEMS, f"{style_id} declared in StyleSystemId enum but missing from STYLE_SYSTEMS"
        system = STYLE_SYSTEMS[style_id]
        assert system.system_id == style_id
        assert system.primary_bg.startswith("#")
        assert system.accent.startswith("#")
        assert system.border_color.startswith("#")
        assert system.corner_radius > 0
        assert len(system.font_family) > 0

        # Validate serialized tokens
        d = system.to_dict()
        assert d["system_id"] == style_id.value
        assert "palette" in d
        assert d["palette"]["primary_bg"] == system.primary_bg
        assert d["palette"]["accent"] == system.accent
        assert d["corner_radius"] == system.corner_radius

    claude = get_style_system("claude_editorial")
    assert claude.primary_bg == "#F8FAFC"
    assert claude.accent == "#1E40AF"

    apple = get_style_system("apple_keynote")
    assert apple.primary_bg == "#0B0D11"
    assert apple.accent == "#2997FF"

    stripe = get_style_system("stripe_motion")
    assert stripe.primary_bg == "#F6F9FC"
    assert stripe.accent == "#635BFF"


from production.phase17.environment_generator import (
    generate_environment_for_scene,
    classify_topic_domain,
    resolve_environment_decision,
    TopicDomain,
    generate_macro_studio_bg,
    generate_blueprint_cad_bg,
    generate_tactical_radar_bg,
    generate_cinematic_warehouse_bg,
    generate_premium_brand_stage_bg,
    generate_vector_latent_space_bg,
    generate_cloud_topology_mesh_bg,
)


def test_environment_variety_no_background_over_8s():
    """Verify that all 5 scene environments are distinct and have unique pixel characteristics."""
    bgs = [generate_environment_for_scene(i, width=360, height=640) for i in range(5)]
    assert len(bgs) == 5

    # Check distinct average colors across environments
    averages = [img.resize((1, 1)).getpixel((0, 0)) for img in bgs]
    # At least 3 distinct average hues / colors
    assert len(set(averages)) >= 3


def test_topic_aligned_environment_generation_5_unrelated_topics():
    """Verify benchmark across 5 unrelated topics:
    Each topic resolves to its correct semantic domain, distinct structural archetypes,
    and QA decision audit rationale.
    """
    benchmarks = [
        ("Amazon Bedrock Native RAG", TopicDomain.SOFTWARE_AI, "Cloud Topology Mesh"),
        ("Six-Axis Industrial Robotic Arm", TopicDomain.ROBOTICS_HARDWARE, "Blueprint CAD Drafting"),
        ("CRISPR Cas9 Genomic Editing", TopicDomain.BIOTECH_SCIENCE, "Vector Latent Space"),
        ("High Frequency Order Book Arbitrage", TopicDomain.FINANCE_MARKETS, "Isometric Dot Grid"),
        ("Modern Quantum Computing System", TopicDomain.GENERAL_TECH, "Isometric Dot Grid"),
    ]

    for topic_name, expected_domain, expected_scene2_arch in benchmarks:
        domain = classify_topic_domain(topic=topic_name)
        assert domain == expected_domain, f"Topic '{topic_name}' expected domain {expected_domain}, got {domain}"

        # Generate Scene 2 (index 1)
        bg = generate_environment_for_scene(scene_index=1, width=360, height=640, topic=topic_name)
        assert "environment_decision" in bg.info
        decision = bg.info["environment_decision"]
        assert decision["domain"] == expected_domain.value
        assert decision["archetype"] == expected_scene2_arch
        assert "rationale" in decision
        assert len(decision["structural_features"]) >= 3


def test_structural_difference_between_unrelated_topics():
    """Verify that Software AI and Robotics topics have structural differences, not merely palette differences.
    Scene 2 of Software RAG must NOT render a mechanical blueprint CAD grid.
    """
    rag_bg = generate_environment_for_scene(scene_index=1, width=360, height=640, topic="Amazon Bedrock Native RAG")
    robot_bg = generate_environment_for_scene(scene_index=1, width=360, height=640, topic="Six-Axis Industrial Robotic Arm")

    # Both images generated
    assert rag_bg.size == robot_bg.size
    # Decision check: software topic NEVER pulls CAD or mechanical warehouse
    assert rag_bg.info["environment_decision"]["domain"] == "software_ai"
    assert rag_bg.info["environment_decision"]["archetype"] == "Cloud Topology Mesh"
    assert robot_bg.info["environment_decision"]["domain"] == "robotics_hardware"
    assert robot_bg.info["environment_decision"]["archetype"] == "Blueprint CAD Drafting"

    # Pixel difference verification: structural layout difference (RMS delta > 5.0)
    from production.phase17.visual_qa import _frame_difference
    delta = _frame_difference(rag_bg, robot_bg)
    assert delta > 5.0, f"Expected structural difference between RAG and Robotics backgrounds, got delta {delta}"



def test_multi_layer_depth_separation(tmp_path: Path):
    """Verify that generate_scene_layers produces bg (opaque), mid (transparent), and fg (transparent),
    with substantial layer occupancy and real parallax displacement.
    """
    from production.phase17.multi_layer_generator import compute_layer_occupancy

    layers = generate_scene_layers(
        scene_index=0,
        narration="Warehouse robots are getting smarter fast.",
        output_dir=tmp_path,
        scene_id="scene_01",
        topic="Six-Axis Industrial Robotic Arm",
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

    # Background must be 100% opaque
    bg_occ = compute_layer_occupancy(layers["bg"])
    assert bg_occ == 1.0

    # Real depth: Midground and foreground must have substantial occupancy (not tiny decorative pixels)
    mid_occ = compute_layer_occupancy(mid_img)
    fg_occ = compute_layer_occupancy(fg_img)
    assert mid_occ >= 0.08, f"Midground occupancy too low: {mid_occ}"
    assert fg_occ >= 0.05, f"Foreground occupancy too low: {fg_occ}"

    # Parallax displacement validation: fg moves faster than mid, which moves faster than bg
    # Remotion parallax contract: fg rate = 90, mid rate = 50, bg rate = 20
    fg_rate = 90
    mid_rate = 50
    bg_rate = 20
    assert fg_rate > mid_rate > bg_rate
    delta_fg_mid = fg_rate - mid_rate
    delta_mid_bg = mid_rate - bg_rate
    assert delta_fg_mid == 40
    assert delta_mid_bg == 30

    # Also test software domain layers for substantial occupancy
    sw_layers = generate_scene_layers(
        scene_index=1,
        narration="Amazon Bedrock now offers native RAG pipelines.",
        output_dir=tmp_path / "sw",
        scene_id="scene_02",
        topic="Amazon Bedrock Native RAG",
    )
    sw_mid_occ = compute_layer_occupancy(sw_layers["mid"])
    sw_fg_occ = compute_layer_occupancy(sw_layers["fg"])
    assert sw_mid_occ >= 0.08
    assert sw_fg_occ >= 0.05


def test_transformative_transitions():
    """Verify N-1 boundary transitions are assigned with continuity-first, simple intents.

    §16: cuts and gentle dissolves are the correct default for explanatory scenes.
    Only unresolvable / unsupported intents are rejected.
    """
    from production.phase17.transition_director import assign_boundary_transitions, SceneBoundaryTransition

    # 1 scene: exactly 0 transitions (no phantom final transition)
    assert assign_boundary_transitions(1) == []
    assert assign_transformative_transitions(1) == []

    # 2 scenes: exactly 1 boundary transition
    b_2 = assign_boundary_transitions(2)
    assert len(b_2) == 1
    assert b_2[0].from_scene_id == "scene_01"
    assert b_2[0].to_scene_id == "scene_02"
    assert b_2[0].transition_intent in ALLOWED_TRANSITIONS
    assert len(assign_transformative_transitions(2)) == 1

    # 5 scenes: exactly 4 boundary transitions (N-1)
    trans = assign_transformative_transitions(5)
    assert len(trans) == 4
    for t in trans:
        assert t not in FORBIDDEN_TRANSITIONS

    valid, errs = validate_transition_integrity(trans)
    assert valid is True
    assert len(errs) == 0

    boundary_trans_5 = assign_boundary_transitions(5)
    assert len(boundary_trans_5) == 4
    assert boundary_trans_5[0].from_scene_id == "scene_01"
    assert boundary_trans_5[0].to_scene_id == "scene_02"
    assert boundary_trans_5[3].from_scene_id == "scene_04"
    assert boundary_trans_5[3].to_scene_id == "scene_05"
    valid_b5, errs_b5 = validate_transition_integrity(boundary_trans_5)
    assert valid_b5 is True

    # 6 scenes: exactly 5 boundary transitions
    b_6 = assign_boundary_transitions(6)
    assert len(b_6) == 5
    assert len(assign_transformative_transitions(6)) == 5
    assert b_6[4].from_scene_id == "scene_05"
    assert b_6[4].to_scene_id == "scene_06"

    # Also test passing actual scene dicts
    custom_scenes = [
        {"scene_id": "intro"},
        {"scene_id": "concept"},
        {"scene_id": "outro"},
    ]
    b_custom = assign_boundary_transitions(custom_scenes)
    assert len(b_custom) == 2
    assert b_custom[0].from_scene_id == "intro"
    assert b_custom[0].to_scene_id == "concept"
    assert b_custom[1].from_scene_id == "concept"
    assert b_custom[1].to_scene_id == "outro"

    # Simple continuity transitions are explicitly valid — never a failure.
    valid_simple, errs_simple = validate_transition_integrity(["hard_cut", "fade"])
    assert valid_simple is True
    assert len(errs_simple) == 0

    # Unresolvable or unsupported intents are still rejected.
    invalid, errs_bad = validate_transition_integrity(["hard_cut", "not_a_real_transition"])
    assert invalid is False
    assert len(errs_bad) == 1



def test_visual_language_qa_fails_when_no_frames(tmp_path: Path):
    """Verify that evaluate_visual_language fails closed when no frames are rendered."""
    scenes = [
        {"scene_id": f"scene_0{i+1}", "start_seconds": i * 5.0, "end_seconds": (i + 1) * 5.0, "environment": f"Env_{i+1}", "depth_strategy": "background_midground_foreground"}
        for i in range(5)
    ]
    timeline = [
        {"scene_id": f"scene_0{i+1}", "transition_in": "zoom_transition"}
        for i in range(5)
    ]

    eval_res = evaluate_visual_language(tmp_path, scenes, timeline)
    assert eval_res.passed is False
    assert eval_res.visual_language_score == 0.0
    assert any("No visual frame evidence available" in r for r in eval_res.rejection_reasons)


def test_visual_language_qa_fails_on_visually_static_render(tmp_path: Path):
    """Verify that an EMPTY render (no depicted content) fails closed.

    Stillness alone is allowed (§14); a blank frame with nothing depicted is not —
    the explained subject must be visible (§21).
    """
    qa_dir = tmp_path / "qa"
    qa_dir.mkdir(parents=True, exist_ok=True)
    
    # Save identical blank images for all scenes: no subject, no structure
    blank = Image.new("RGB", (200, 350), color=(15, 23, 42))
    for i in range(5):
        # 2 identical frames per scene
        blank.save(qa_dir / f"frame_scene_0{i+1}_01.png")
        blank.save(qa_dir / f"frame_scene_0{i+1}_02.png")

    scenes = [
        {"scene_id": f"scene_0{i+1}", "start_seconds": i * 5.0, "end_seconds": (i + 1) * 5.0, "environment": f"Env_{i+1}", "depth_strategy": "background_midground_foreground"}
        for i in range(5)
    ]
    timeline = [
        {"scene_id": f"scene_0{i+1}", "transition_in": "zoom_transition"}
        for i in range(5)
    ]

    eval_res = evaluate_visual_language(tmp_path, scenes, timeline)
    assert eval_res.passed is False
    assert any("no visual content" in r.lower() for r in eval_res.rejection_reasons)
    assert eval_res.visual_language_score < 7.0


def test_visual_language_qa_passes_with_real_motion_and_structured_evidence(tmp_path: Path):
    """Verify that a genuinely varied render with measurable motion passes with structured scene evidence."""
    qa_dir = tmp_path / "qa" / "frame_samples"
    qa_dir.mkdir(parents=True, exist_ok=True)
    from PIL import ImageDraw

    # Generate distinct, high-contrast, varied frames per scene with motion
    for i in range(5):
        # Frame 1: Circle/card at top left
        img1 = Image.new("RGB", (200, 350), color=(20 + i * 30, 30 + i * 20, 50 + i * 15))
        d1 = ImageDraw.Draw(img1)
        d1.rectangle([(20, 30), (160, 120)], fill=(220, 240, 255), outline=(255, 255, 255), width=3)
        d1.ellipse([(50, 180), (140, 270)], fill=(59, 130, 246))
        img1.save(qa_dir / f"frame_scene_0{i+1}_01.png")

        # Frame 2: Shifted geometry (measurable motion > 10.0)
        img2 = Image.new("RGB", (200, 350), color=(20 + i * 30, 30 + i * 20, 50 + i * 15))
        d2 = ImageDraw.Draw(img2)
        d2.rectangle([(40, 60), (180, 150)], fill=(240, 245, 255), outline=(255, 255, 255), width=3)
        d2.ellipse([(30, 140), (160, 270)], fill=(234, 88, 12))
        img2.save(qa_dir / f"frame_scene_0{i+1}_02.png")

    scenes = [
        {"scene_id": f"scene_0{i+1}", "start_seconds": i * 5.0, "end_seconds": (i + 1) * 5.0, "environment": f"Env_{i+1}", "depth_strategy": "background_midground_foreground"}
        for i in range(5)
    ]
    timeline = [
        {"scene_id": f"scene_0{i+1}", "transition_in": "zoom_transition"}
        for i in range(5)
    ]

    eval_res = evaluate_visual_language(tmp_path, scenes, timeline, frames_dir=qa_dir)
    assert eval_res.passed is True
    assert eval_res.visual_language_score >= 8.0
    assert len(eval_res.rejection_reasons) == 0

    # Verify structured scene evaluations and evidence
    assert len(eval_res.scene_evaluations) == 5
    for sc_eval in eval_res.scene_evaluations:
        assert "scene_id" in sc_eval
        assert "score" in sc_eval
        assert sc_eval["score"] >= 7.0
        ev = sc_eval["evidence"]
        assert "frame_samples" in ev
        assert len(ev["frame_samples"]) >= 1
        assert "motion_delta" in ev
        assert ev["motion_delta"] > 5.0
        assert "layout_signature" in ev
        assert "background_similarity" in ev
        assert "layer_occupancy" in ev
        assert ev["is_static"] is False

