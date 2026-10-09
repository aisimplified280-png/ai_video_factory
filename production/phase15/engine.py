"""Phase 15/15B Visual Intelligence & Claim Grounding Engine — Orchestrator.

Converts script sections and research facts into a rich, non-repetitive,
and rigorously claim-grounded visual plan.
Implements automatic replanning (Phase 15B Step 21) when visual grounding (< 7.0)
or claim coverage (< 80%) or visual diversity is weak.
"""
from __future__ import annotations

from typing import Any
from .models import SceneVisualPlan, VisualScorecard
from .semantic_analyzer import analyze_scene_intent
from .shot_director import ShotDirector
from .frame_qa import evaluate_visual_diversity


def generate_phase15_plan(
    script_data: dict,
    prod_state: dict,
    max_retries: int = 3,
) -> dict[str, Any]:
    """Execute Phase 15B Visual Intelligence & Claim Grounding pipeline with automatic replanning."""
    sections = script_data.get("data", {}).get("sections", [])
    if not sections and "sections" in script_data:
        sections = script_data["sections"]

    topic = prod_state.get("topic") or script_data.get("data", {}).get("primary_subject") or "Frontier AI"
    research_data = prod_state.get("research_data", {})
    research_context = ""
    research_pack = None
    if isinstance(research_data, dict):
        research_pack = research_data
        if research_data.get("topic"):
            topic = research_data["topic"]
        stories = research_data.get("stories", [])
        if stories:
            research_context = " ".join(s.get("summary", "") + " " + s.get("headline", "") for s in stories)
        claims = research_data.get("claims", [])
        if claims:
            research_context += " " + " ".join(c.get("claim", "") for c in claims)

    total_scenes = len(sections)

    # 1. Semantic Scene Intent & Claim Grounding Extraction (Phase 15B Step 2)
    intents = [
        analyze_scene_intent(
            sec,
            i,
            total_scenes,
            topic,
            research_context,
            research_pack=research_pack,
        )
        for i, sec in enumerate(sections)
    ]

    # 2. Shot Direction & Grounding Evaluation with Automatic Replanning Loop (Phase 15B Step 21)
    director = ShotDirector()
    scene_plans = director.direct_scenes(intents, topic)
    scorecard = evaluate_visual_diversity(scene_plans, topic=topic)
    replan_count = 0

    while (
        (not scorecard.passed or scorecard.visual_grounding < 7.0 or scorecard.claim_coverage < 0.75 or scorecard.visual_diversity < 4.0)
        and replan_count < max_retries
    ):
        replan_count += 1
        # Extract rejection reasons to guide next iteration
        rejection_reasons = scorecard.rejection_reason or "Low claim grounding or low diversity"
        # Re-direct with fresh visual memory and alternative modes
        scene_plans = director.direct_scenes(intents, topic)
        scorecard = evaluate_visual_diversity(scene_plans, topic=topic)

    # 3. Format canonical plan output with claim grounding metadata
    concepts = []
    for p in scene_plans:
        concepts.append({
            "scene_id": p.scene_id,
            "section_id": p.section_id,
            "narrative_role": p.narrative_role,
            "visual_intent": p.visual_intent,
            "visual_mode": p.visual_mode.value,
            "subject": p.subject,
            "action": p.action,
            "environment": p.environment,
            "shot_type": p.shot_type,
            "camera_angle": p.camera_angle,
            "camera_motion": p.camera_motion,
            "lens_feel": p.lens_feel,
            "composition": p.composition,
            "depth": p.depth,
            "lighting": p.lighting,
            "motion_intensity": p.motion_intensity,
            "transition_in": p.transition_in,
            "transition_out": p.transition_out,
            "overlay_strategy": p.overlay_strategy,
            "graphic_strategy": p.graphic_strategy,
            "asset_strategy": p.asset_strategy,
            "visual_prompt": p.visual_prompt,
            "negative_constraints": p.negative_constraints,
            "avoid_repetition": p.avoid_repetition,
            # Claim Grounding Metadata (Phase 15B)
            "claim_id": p.claim_id,
            "claim_type": p.claim_type,
            "entities": p.entities,
            "relationship": p.relationship,
            "required_visual_evidence": p.required_visual_evidence,
            "unacceptable_visuals": p.unacceptable_visuals,
            "grounding_level": p.grounding_level,
            "visual_grounding_score": p.visual_grounding_score,
            "claim_coverage_score": p.claim_coverage_score,
            # Backward-compatibility aliases
            "visual_story": f"{p.action} in {p.environment}",
            "visual_metaphor": p.visual_metaphor,
            "motion_intent": p.motion_intent,
            "overlay_intent": p.overlay_strategy,
            "background_prompt": p.visual_prompt,
            "camera_movement": p.camera_motion,
            "subject_action": p.action,
            "scene_breakdown": p.scene_breakdown,
            "supporting_graphics": [],
        })

    unique_envs = len({c["environment"] for c in concepts})
    unique_subjs = len({c["subject"] for c in concepts})
    unique_modes = len({c["visual_mode"] for c in concepts})
    unique_actions = len({c["action"] for c in concepts})
    diversity_ratio = round(
        max(
            scorecard.visual_diversity / 10.0,
            (unique_envs + unique_subjs + unique_actions) / (3.0 * max(1, total_scenes)),
        ),
        2,
    )

    return {
        "schema_version": "2.0",
        "phase": "phase_15b_claim_grounding",
        "replans_attempted": replan_count,
        "scene_concepts": concepts,
        "visual_scorecard": scorecard.model_dump(),
        "claim_visual_qa_report": [e.model_dump() for e in scorecard.scene_evaluations],
        "diversity_metrics": {
            "target_met": scorecard.passed,
            "scene_diversity_ratio": diversity_ratio,
            "unique_locations": unique_envs,
            "unique_environments": unique_envs,
            "unique_subjects": unique_subjs,
            "unique_actions": len({c["action"] for c in concepts}),
            "unique_visual_modes": unique_modes,
            "visual_grounding_score": scorecard.visual_grounding,
            "claim_coverage_score": scorecard.claim_coverage,
            "overall_visual_direction_score": scorecard.overall_visual_direction,
        },
        "emphasis_cues": [],
        "retention_notes": [],
    }
