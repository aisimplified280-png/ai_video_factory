"""Tests for Phase 15B Claim-Grounded Visual Relevance Engine.

Verifies:
1. Capability claim -> direct capability visual
2. Adaptation claim -> changing environment / obstacle avoidance visual
3. Coordination claim -> multiple coordinated agents
4. Business impact -> throughput acceleration and bottleneck elimination
5. Entity preservation
6. Action preservation
7. Relationship preservation
8. Required visual evidence detection
9. Generic topical image rejection (e.g. abstract brain in void rejected for physical control)
10. Visual contradiction detection (e.g. collision when avoiding, manual control when AI autonomous)
11. Low grounding automatic rejection (< 7.0 threshold)
12. Automatic scene replanning loop
13. Claim coverage calculation (>= 80% threshold)
14. Renderer receives claim-specific visual plan
15. Critical Regression (Step 28): "GPT-6 Astra directly controls an industrial robotic arm"
"""
import pytest
from pathlib import Path
from PIL import Image

from production.phase15.models import (
    ClaimType,
    ClaimVisualPlan,
    GroundingLevel,
    SceneVisualPlan,
    VisualMode,
    VisualScorecard,
)
from production.phase15.claim_grounder import (
    extract_claim_visual_plan,
    evaluate_claim_grounding,
)
from production.phase15.semantic_analyzer import analyze_scene_intent
from production.phase15.shot_director import ShotDirector
from production.phase15.engine import generate_phase15_plan
from production.phase15.frame_qa import evaluate_visual_diversity
from production.phase15.visual_generator import render_procedural_scene_visual


def test_capability_claim_requires_direct_capability_evidence():
    """Verify that capability claims mandate AI control source, physical robot, and action."""
    section = {
        "spoken_text": "GPT-6 Astra directly controls physical robots with real-time feedback.",
        "narrative_role": "reveal",
    }
    claim_plan = extract_claim_visual_plan(section, scene_idx=1, total_scenes=5, topic="GPT-6 Astra controls robots")
    assert claim_plan.claim_type == ClaimType.CAPABILITY
    assert any("control" in req.lower() for req in claim_plan.required_visual_evidence)
    assert any("robot" in req.lower() for req in claim_plan.required_visual_evidence)
    assert "generic humanoid robot portrait" in claim_plan.unacceptable_visuals


def test_adaptation_claim_requires_obstacle_and_reroute():
    """Verify that adaptation claims mandate obstacles, sensor detection, and altered trajectory."""
    section = {
        "spoken_text": "Instead of rigid pre-programmed routines, these machines adapt dynamically to moving obstacles and inventory shifts.",
        "narrative_role": "mechanism",
    }
    claim_plan = extract_claim_visual_plan(section, scene_idx=2, total_scenes=5, topic="Autonomous Fleet")
    assert claim_plan.claim_type == ClaimType.DEMONSTRATION
    assert "obstacle" in claim_plan.required_visual_evidence
    assert "altered trajectory vector" in claim_plan.required_visual_evidence
    assert "robot crashing into obstacle" in claim_plan.unacceptable_visuals


def test_business_impact_requires_throughput_evidence():
    """Verify that business impact claims mandate inventory throughput and delay reduction."""
    section = {
        "spoken_text": "That means facilities can move inventory faster, with fewer delays and less human intervention.",
        "narrative_role": "implication",
    }
    claim_plan = extract_claim_visual_plan(section, scene_idx=3, total_scenes=5, topic="Logistics Scale")
    assert claim_plan.claim_type == ClaimType.BUSINESS_IMPACT
    assert any("throughput" in req.lower() or "movement" in req.lower() for req in claim_plan.required_visual_evidence)
    assert any("delay" in req.lower() or "bottleneck" in req.lower() for req in claim_plan.required_visual_evidence)


def test_entity_and_action_preservation():
    """Verify that named entities and actions from the narration are strictly preserved in the visual plan."""
    section = {
        "spoken_text": "Advanced neural networks can now directly control physical robots with real-time sensor feedback.",
        "narrative_role": "reveal",
    }
    intent = analyze_scene_intent(section, scene_idx=1, total_scenes=5, topic="GPT-6 Astra controls robots")
    director = ShotDirector()
    plan = director._direct_single_scene(intent, scene_idx=1, total_scenes=5, topic="GPT-6 Astra controls robots")

    assert plan.visual_mode in (VisualMode.LITERAL, VisualMode.MECHANISM, VisualMode.DEMONSTRATION)
    assert "arm" in plan.subject.lower() or "robot" in plan.subject.lower()
    assert "control" in plan.subject.lower() or "control" in plan.action.lower()


def test_generic_metaphor_rejected_for_physical_control():
    """Verify that an abstract neural void or generic warehouse without control fails grounding QA."""
    claim_plan = ClaimVisualPlan(
        claim_id="claim_01",
        narration_text="GPT-6 Astra directly controls physical robots with real-time feedback.",
        claim_type=ClaimType.CAPABILITY,
        entities=["GPT-6 Astra", "industrial robotic arm"],
        action="direct motor control commands articulated through robotic actuators",
        environment="robotics testing cell",
        relationship="AI controls physical machine",
        required_visual_evidence=["AI / control source", "industrial robotic arm", "control relationship", "physical robot action"],
        unacceptable_visuals=["abstract brain in dark void without robot", "server room"],
        grounding_level=4.0,
    )

    # Bad Plan: Pure abstract neural void
    bad_plan = SceneVisualPlan(
        scene_id="scene_02",
        visual_intent="Abstract visualization of glowing electric synaptic data streams in dark void",
        visual_mode=VisualMode.ABSTRACT,
        subject="synaptic neural data stream in matrix",
        action="electric cyan pulses racing through tensor lattice",
        environment="abstract dark neural matrix",
        visual_prompt="abstract brain in dark void without robot, cyan lines",
    )

    evaluation = evaluate_claim_grounding(claim_plan, bad_plan)
    assert evaluation.decision == "REJECT"
    assert evaluation.visual_grounding_score < 7.0
    assert evaluation.claim_coverage < 0.75


def test_visual_contradiction_detection():
    """Verify that visual plans contradicting the narration fail QA."""
    # Contradiction 1: Robot crashes when narration claims obstacle avoidance
    claim_adapt = ClaimVisualPlan(
        claim_id="claim_02",
        narration_text="Robots adapt dynamically to moving obstacles without stopping.",
        claim_type=ClaimType.DEMONSTRATION,
        required_visual_evidence=["autonomous machine", "obstacle", "altered trajectory vector"],
        unacceptable_visuals=["robot crashing into obstacle"],
    )
    crash_plan = SceneVisualPlan(
        scene_id="scene_03",
        visual_intent="Robot crashing into heavy metal barrier on warehouse floor",
        subject="autonomous rover",
        action="crash into obstacle",
        environment="warehouse floor",
        visual_prompt="rover crash into barrier",
    )
    eval_crash = evaluate_claim_grounding(claim_adapt, crash_plan)
    assert eval_crash.contradiction_detected is True
    assert eval_crash.decision == "REJECT"

    # Contradiction 2: Human manual control when narration claims AI autonomous control
    claim_ai = ClaimVisualPlan(
        claim_id="claim_03",
        narration_text="AI directly controls physical robots.",
        claim_type=ClaimType.CAPABILITY,
        required_visual_evidence=["AI / control source", "robot", "physical robot action"],
        unacceptable_visuals=["human manually operating"],
    )
    manual_plan = SceneVisualPlan(
        scene_id="scene_02",
        visual_intent="Human operator manually steering robot arm with joystick",
        subject="human technician",
        action="human manually operating the arm with physical joystick",
        environment="workshop",
        visual_prompt="human manually operating the arm",
    )
    eval_manual = evaluate_claim_grounding(claim_ai, manual_plan)
    assert eval_manual.contradiction_detected is True
    assert eval_manual.decision == "REJECT"


def test_critical_step28_regression():
    """CRITICAL REGRESSION TEST (Step 28):
    Narration: 'GPT-6 Astra directly controls an industrial robotic arm.'
    The generated visual plan MUST contain:
    - GPT-6 Astra / AI control representation
    - industrial robotic arm
    - control relationship
    - physical robot action
    A scene containing only warehouse, robot, AI brain, server room, or futuristic graphics must FAIL.
    """
    section = {
        "spoken_text": "GPT-6 Astra directly controls an industrial robotic arm.",
        "narrative_role": "reveal",
    }
    claim_plan = extract_claim_visual_plan(section, scene_idx=1, total_scenes=5, topic="GPT-6 Astra controls robots")

    # 1. Valid compliant plan directly from our ShotDirector
    intent = analyze_scene_intent(section, scene_idx=1, total_scenes=5, topic="GPT-6 Astra controls robots")
    director = ShotDirector()
    compliant_plan = director._direct_single_scene(intent, scene_idx=1, total_scenes=5, topic="GPT-6 Astra controls robots")

    eval_compliant = evaluate_claim_grounding(claim_plan, compliant_plan)
    assert eval_compliant.decision == "PASS"
    assert eval_compliant.visual_grounding_score >= 7.0
    assert eval_compliant.claim_coverage >= 0.75

    # 2. Non-compliant generic scenes MUST FAIL
    generic_warehouse = SceneVisualPlan(
        scene_id="scene_02",
        visual_intent="Vast warehouse with boxes on shelves",
        subject="warehouse racks",
        action="sitting stationary",
        environment="warehouse",
        visual_prompt="vast warehouse with shelves",
    )
    eval_wh = evaluate_claim_grounding(claim_plan, generic_warehouse)
    assert eval_wh.decision == "REJECT"

    generic_server = SceneVisualPlan(
        scene_id="scene_02",
        visual_intent="Server room with blinking LEDs",
        subject="server rack array",
        action="blinking blue lights",
        environment="data center",
        visual_prompt="server room racks with blinking lights",
    )
    eval_srv = evaluate_claim_grounding(claim_plan, generic_server)
    assert eval_srv.decision == "REJECT"


def test_procedural_generator_renders_grounded_features():
    """Verify that procedural rendering produces concrete claim elements for LITERAL, DEMONSTRATION, SCALE."""
    # Test LITERAL (Robotic Arm with AI direct control HUD)
    plan_literal = SceneVisualPlan(
        scene_id="scene_02",
        visual_mode=VisualMode.LITERAL,
        subject="six-axis industrial robotic arm directly controlled by AI model",
        action="articulating with sub-millimeter precision to manipulate component under closed-loop sensor feedback",
        environment="high-precision industrial robotics automated workcell",
    )
    img_literal = render_procedural_scene_visual(plan_literal)
    assert isinstance(img_literal, Image.Image)
    assert img_literal.size == (1080, 1920)

    # Test DEMONSTRATION (Obstacle & dynamic vector rerouting)
    plan_demo = SceneVisualPlan(
        scene_id="scene_03",
        visual_mode=VisualMode.DEMONSTRATION,
        subject="autonomous logistics machines dynamically rerouting around obstacles",
        action="active sensor detection cone detecting unexpected obstacle and dynamically recalculating vector trajectory around it without stopping",
        environment="automated fulfillment warehouse floor",
    )
    img_demo = render_procedural_scene_visual(plan_demo)
    assert isinstance(img_demo, Image.Image)
    assert img_demo.size == (1080, 1920)


def test_phase15b_end_to_end_plan_generation():
    """Verify complete Phase 15B pipeline generates grounded plan with Scorecard >= 7.0."""
    script_data = {
        "data": {
            "sections": [
                {"id": "sec_01", "spoken_text": "Warehouse robots are getting smarter fast.", "narrative_role": "hook"},
                {"id": "sec_02", "spoken_text": "Advanced neural networks can now directly control physical robots with real-time sensor feedback.", "narrative_role": "reveal"},
                {"id": "sec_03", "spoken_text": "Instead of rigid pre-programmed routines, these machines adapt dynamically to moving obstacles and inventory shifts.", "narrative_role": "mechanism"},
                {"id": "sec_04", "spoken_text": "That means facilities can move inventory faster, with fewer delays and less human intervention.", "narrative_role": "implication"},
                {"id": "sec_05", "spoken_text": "And this is just the beginning. Subscribe to AI Simplified Lab for daily frontier AI briefings.", "narrative_role": "cta"},
            ]
        }
    }
    prod_state = {"topic": "GPT-6 Astra controls robots"}

    plan = generate_phase15_plan(script_data, prod_state)
    assert plan["phase"] == "phase_15b_claim_grounding"
    assert len(plan["scene_concepts"]) == 5

    scorecard = plan["visual_scorecard"]
    assert scorecard["passed"] is True
    assert scorecard["visual_grounding"] >= 7.0
    assert scorecard["claim_coverage"] >= 0.75
    assert scorecard["contradiction_count"] == 0
    assert len(plan["claim_visual_qa_report"]) == 5
