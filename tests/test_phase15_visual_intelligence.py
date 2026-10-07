"""Test suite for Phase 15 Visual Intelligence & Diversity Engine."""
from __future__ import annotations

from pathlib import Path
from PIL import Image
import pytest

from production.phase15.models import VisualMode, SceneVisualPlan
from production.phase15.semantic_analyzer import analyze_scene_intent
from production.phase15.shot_director import ShotDirector, VisualMemory
from production.phase15.frame_qa import evaluate_visual_diversity, _compute_histogram_correlation
from production.phase15.engine import generate_phase15_plan
from production.phase15.visual_generator import render_procedural_scene_visual


def test_five_scene_story_never_collapses():
    """Verify that a 5-scene story cannot collapse into visually similar outputs."""
    script_data = {
        "data": {
            "primary_subject": "GPT-6 Astra controls robots",
            "sections": [
                {
                    "section_id": "sec_01",
                    "scene_id": "scene_01",
                    "narrative_role": "hook",
                    "spoken_text": "Warehouse robots are getting smarter fast.",
                    "primary_intent": "emerge",
                    "emphasis_words": ["ROBOTS", "SMARTER"],
                },
                {
                    "section_id": "sec_02",
                    "scene_id": "scene_02",
                    "narrative_role": "reveal",
                    "spoken_text": "Advanced neural networks can now directly control physical robots with real-time sensor feedback.",
                    "primary_intent": "dolly_through",
                    "emphasis_words": ["NEURAL", "DIRECT"],
                },
                {
                    "section_id": "sec_03",
                    "scene_id": "scene_03",
                    "narrative_role": "mechanism",
                    "spoken_text": "Instead of rigid pre-programmed routines, these machines adapt dynamically to moving obstacles and inventory shifts.",
                    "primary_intent": "dynamic_track",
                    "emphasis_words": ["ADAPT", "DYNAMICALLY"],
                },
                {
                    "section_id": "sec_04",
                    "scene_id": "scene_04",
                    "narrative_role": "implication",
                    "spoken_text": "That means facilities can move inventory faster, with fewer delays and less human intervention.",
                    "primary_intent": "scale_up",
                    "emphasis_words": ["FASTER", "FEWER_DELAYS"],
                },
                {
                    "section_id": "sec_05",
                    "scene_id": "scene_05",
                    "narrative_role": "cta",
                    "spoken_text": "And this is just the beginning. Subscribe to AI Simplified Lab for daily frontier AI briefings.",
                    "primary_intent": "brand_lock",
                    "emphasis_words": ["SUBSCRIBE", "DAILY"],
                },
            ],
        }
    }

    prod_state = {
        "topic": "GPT-6 Astra controls robots",
        "research_data": {
            "stories": [{"summary": "GPT-6 Astra directly controls industrial robot arms with low latency."}]
        },
    }

    plan = generate_phase15_plan(script_data, prod_state)
    concepts = plan["scene_concepts"]

    assert len(concepts) == 5

    # 1. Visual Modes must be distinct across scenes
    modes = [c["visual_mode"] for c in concepts]
    assert len(set(modes)) >= 4, f"Expected at least 4 distinct visual modes, got {set(modes)}"
    assert modes[0] == VisualMode.DETAIL.value  # Hook = Detail / Macro
    assert modes[1] in (VisualMode.LITERAL.value, VisualMode.METAPHOR.value)  # Reveal = Literal capability or Metaphor
    assert modes[2] == VisualMode.DEMONSTRATION.value  # Mechanism = Demonstration
    assert modes[3] == VisualMode.SCALE.value  # Implication = Scale
    assert modes[4] == VisualMode.BRAND_CTA.value  # CTA = Brand/CTA

    # 2. Shot types must be completely unique
    shot_types = [c["shot_type"] for c in concepts]
    assert len(set(shot_types)) == 5

    # 3. Environments must be completely unique
    environments = [c["environment"] for c in concepts]
    assert len(set(environments)) == 5

    # 4. Subjects must be completely unique (not all "robot arm")
    subjects = [c["subject"] for c in concepts]
    assert len(set(subjects)) == 5
    # Scene 2 must depict neural control or robot mechanism
    assert "neural" in subjects[1].lower() or "robot" in subjects[1].lower() or "arm" in subjects[1].lower()
    # Scene 5 must be brand/insignia or channel name
    assert "brand" in subjects[4].lower() or "insignia" in subjects[4].lower() or "simplified" in subjects[4].lower()

    # 5. Camera movements must be diverse
    cameras = [c["camera_motion"] for c in concepts]
    assert len(set(cameras)) >= 4

    # 6. Scorecard verification
    scorecard = plan["visual_scorecard"]
    assert scorecard["passed"] is True
    assert scorecard["visual_diversity"] >= 8.0
    assert scorecard["overall_visual_direction"] >= 8.0


def test_consecutive_visual_mode_constraint():
    """Verify that > 2 consecutive scenes of identical mode triggers rejection."""
    repetitive_plans = [
        SceneVisualPlan(
            scene_id=f"scene_{i:02d}",
            section_id=f"sec_{i:02d}",
            visual_mode=VisualMode.LITERAL,
            shot_type="generic_shot",
            camera_angle="eye_level",
            camera_motion="approach_subject",
            composition="center",
            subject="robot arm",
            action="moving",
            environment="factory",
            visual_metaphor="work",
            lighting="neutral",
        )
        for i in range(3)
    ]

    scorecard = evaluate_visual_diversity(repetitive_plans)
    assert scorecard.passed is False
    assert scorecard.rejection_reason is not None
    assert "consecutive scenes" in scorecard.rejection_reason.lower() or "visual diversity score" in scorecard.rejection_reason.lower()


def test_frame_histogram_divergence():
    """Verify that procedural rendering produces chromatic divergence across scenes."""
    director = ShotDirector()
    intents = [
        analyze_scene_intent({"section_id": "sec_01", "spoken_text": "Robots fast.", "narrative_role": "hook"}, 0, 5, "Robots"),
        analyze_scene_intent({"section_id": "sec_02", "spoken_text": "Neural signals flowing.", "narrative_role": "reveal"}, 1, 5, "Robots"),
        analyze_scene_intent({"section_id": "sec_03", "spoken_text": "Fleet adapts.", "narrative_role": "mechanism"}, 2, 5, "Robots"),
    ]
    plans = director.direct_scenes(intents, "Robots")

    img1 = render_procedural_scene_visual(plans[0])  # Detail (metallic titanium + cyan laser)
    img2 = render_procedural_scene_visual(plans[1])  # Metaphor (deep space + neural nodes)
    img3 = render_procedural_scene_visual(plans[2])  # Demonstration (isometric warehouse + yellow lanes)

    corr_1_2 = _compute_histogram_correlation(img1, img2)
    corr_2_3 = _compute_histogram_correlation(img2, img3)

    # High visual diversity implies low correlation between consecutive scene frames
    assert corr_1_2 < 0.70
    assert corr_2_3 < 0.70


def test_repetition_penalties_discourage_duplicate_options():
    """Step 5: Verify that weighted repetition penalties correctly downgrade duplicate options."""
    memory = VisualMemory()
    plan_prev = SceneVisualPlan(
        scene_id="scene_01",
        visual_mode=VisualMode.DETAIL,
        shot_type="extreme_macro_probe",
        camera_motion="fast_push_in",
        composition="tight_macro_crop",
        environment="high-precision testing rig",
        subject="precision robotic gripper",
    )
    memory.record(plan_prev)

    duplicate_opt = {
        "shot_type": "extreme_macro_probe",
        "camera_motion": "fast_push_in",
        "composition": "tight_macro_crop",
        "environment": "high-precision testing rig",
        "subject": "precision robotic gripper",
    }
    penalty = memory.compute_repetition_penalty(duplicate_opt, VisualMode.DETAIL)
    # Mode (-2) + Shot (-2) + Cam (-2) + Comp (-2) + Env (-1) + Subj (-1) = -10.0
    assert penalty == -10.0

    distinct_opt = {
        "shot_type": "wide_isometric_tracking",
        "camera_motion": "overhead_track",
        "composition": "wide_isometric_plane",
        "environment": "automated warehouse",
        "subject": "fleet of rovers",
    }
    penalty_distinct = memory.compute_repetition_penalty(distinct_opt, VisualMode.DEMONSTRATION)
    assert penalty_distinct == 0.0


def test_hook_and_cta_dedicated_treatments():
    """Steps 12 & 13: Verify that Hook receives no initial text overlay and CTA has brand treatment."""
    director = ShotDirector()
    intents = [
        analyze_scene_intent({"section_id": "sec_01", "spoken_text": "Robots moving fast.", "narrative_role": "hook"}, 0, 5, "Robots"),
        analyze_scene_intent({"section_id": "sec_05", "spoken_text": "Subscribe to AI Simplified Lab.", "narrative_role": "cta"}, 4, 5, "Robots"),
    ]
    plans = director.direct_scenes(intents, "Robots")
    assert plans[0].visual_mode == VisualMode.DETAIL
    assert plans[0].overlay_strategy == "none_initial_cut"

    assert plans[1].visual_mode == VisualMode.BRAND_CTA
    assert plans[1].overlay_strategy == "brand_lock"


def test_renderer_consumes_framing_and_camera_intents():
    """Step 17: Verify Remotion SceneComposition.tsx and ImageLayer.tsx consume framing and camera intents."""
    composer_dir = Path(__file__).resolve().parent.parent / "remotion-composer" / "src"
    scene_comp = (composer_dir / "compositions" / "SceneComposition.tsx").read_text(encoding="utf-8")
    img_layer = (composer_dir / "primitives" / "ImageLayer.tsx").read_text(encoding="utf-8")

    assert "pullOut" in scene_comp
    assert "framing={event.framing}" in scene_comp
    assert "framing" in img_layer
    assert "scale(" in img_layer


def test_weak_visual_plan_triggers_replanning():
    """Step 15: Verify that weak diversity triggers the automatic replanning loop."""
    script_data = {
        "data": {
            "sections": [
                {"section_id": "sec_01", "spoken_text": "Story 1", "narrative_role": "hook"},
                {"section_id": "sec_02", "spoken_text": "Story 2", "narrative_role": "reveal"},
            ]
        }
    }
    prod_state = {"topic": "AI Hardware"}
    plan = generate_phase15_plan(script_data, prod_state, max_retries=3)
    assert "replans_attempted" in plan
    assert plan["visual_scorecard"]["passed"] is True
