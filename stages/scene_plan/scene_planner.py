"""Scene Planner — transforms script beats into an editorial shot-by-shot scene plan.

Implements StageHandler for the 'scene_plan' stage.
Consumes:
- script (required)
- art_direction (required)
- proposal_packet (contextual)
- research_brief (contextual)
Produces:
- scene_plan artifact with shot coverage, semantic intents, and governed variety.
"""
from __future__ import annotations

import hashlib
from typing import Any

import models
from schemas.models.artifact import ArtifactEnvelope, ProducerInfo
from schemas.models.common import ProducerKind
from schemas.models.production import ProductionState
from production.stage_registry import StageHandler, StageHandlerResult, StageResultStatus
from stages.scene_plan.beat_analyzer import generate_scene_shots
from stages.scene_plan.scene_prompts import (
    SCENE_PLAN_SYSTEM_PROMPT,
    VALID_CAMERA_INTENTS,
    VALID_MOTION_INTENTS,
    VALID_SCENE_TYPES,
    VALID_VISUAL_TECHNIQUES,
    build_scene_plan_prompt,
)
from stages.scene_plan.scene_validator import SceneValidator
from stages.scene_plan.variety_governor import VarietyGovernor


def _enforce_variety_reconciliation(scenes: list[dict[str, Any]]) -> None:
    """Enforce Variety Governor requirements by breaking repetitive runs."""
    if len(scenes) < 3:
        return

    # 1. Break consecutive identical scene types
    for i in range(2, len(scenes)):
        if scenes[i].get("type") == scenes[i - 1].get("type") == scenes[i - 2].get("type"):
            role = scenes[i].get("narrative_role", "")
            if role == "cta":
                scenes[i]["type"] = "text_card"
            elif scenes[i - 1].get("type") == "animation":
                scenes[i]["type"] = "diagram" if role in ("mechanism", "process", "tension") else "broll"
            elif scenes[i - 1].get("type") == "diagram":
                scenes[i]["type"] = "animation" if role in ("reveal", "payoff") else "generated"
            else:
                scenes[i]["type"] = "diagram"

    # 2. Break consecutive identical visual techniques
    alt_techs = [
        "cinematic_broll",
        "diagram_reveal",
        "system_assembly",
        "analogy_visualization",
        "evidence_wall",
        "network_build",
        "scale_transition",
        "kinetic_typography",
    ]
    for i in range(2, len(scenes)):
        if scenes[i].get("visual_technique") == scenes[i - 1].get("visual_technique") == scenes[i - 2].get("visual_technique"):
            prev_tech = scenes[i - 1].get("visual_technique")
            for t in alt_techs:
                if t != prev_tech:
                    scenes[i]["visual_technique"] = t
                    break

    # 3. Ensure at least 3 distinct techniques across video
    distinct_techs = {s.get("visual_technique") for s in scenes if s.get("visual_technique")}
    if len(distinct_techs) < 3 and len(scenes) >= 3:
        for idx, sc in enumerate(scenes):
            if sc.get("narrative_role") == "cta":
                sc["visual_technique"] = "kinetic_typography"
            elif idx == 0:
                sc["visual_technique"] = "cinematic_broll"
            elif idx == 1:
                sc["visual_technique"] = "diagram_reveal"
            elif idx == 2:
                sc["visual_technique"] = "system_assembly"

    # 4. Break consecutive identical compositions
    alt_compositions = [
        "wide asymmetrical layout",
        "split-screen dynamic",
        "macro focal detail",
        "isometric system view",
        "centered focal hierarchy",
    ]
    for i in range(2, len(scenes)):
        if scenes[i].get("composition_intent") == scenes[i - 1].get("composition_intent") == scenes[i - 2].get("composition_intent"):
            scenes[i]["composition_intent"] = alt_compositions[i % len(alt_compositions)]


class ScenePlanHandler:
    """Production stage handler for editorial scene planning."""

    def __init__(
        self,
        llm_caller: Any | None = None,
        variety_governor: VarietyGovernor | None = None,
    ) -> None:
        self.llm_caller = llm_caller or models.call_llm_json
        self.variety_governor = variety_governor or VarietyGovernor()
        self.validator = SceneValidator(variety_governor=self.variety_governor)

    def run(
        self,
        stage_name: str,
        state: ProductionState,
        inputs: dict[str, ArtifactEnvelope],
        **kwargs: Any,
    ) -> StageHandlerResult:
        # 1. Validate upstream required artifacts
        script_art = inputs.get("script")
        if not script_art or not script_art.data:
            return StageHandlerResult(
                status=StageResultStatus.BLOCKED,
                message="Scene plan blocked: missing required 'script' artifact.",
                errors=["MISSING_UPSTREAM_SCRIPT"],
            )

        art_direction_art = inputs.get("art_direction")
        if not art_direction_art or not art_direction_art.data:
            return StageHandlerResult(
                status=StageResultStatus.BLOCKED,
                message="Scene plan blocked: missing required 'art_direction' artifact.",
                errors=["MISSING_UPSTREAM_ART_DIRECTION"],
            )

        proposal_art = inputs.get("proposal_packet")
        research_art = inputs.get("research_brief")

        script_data = script_art.data
        art_direction_data = art_direction_art.data
        sections = script_data.get("sections", [])
        if not sections:
            return StageHandlerResult(
                status=StageResultStatus.BLOCKED,
                message="Scene plan blocked: script contains no narrative sections.",
                errors=["EMPTY_SCRIPT_SECTIONS"],
            )

        # Selected concept resolution
        selected_concept: dict[str, Any] = {}
        if proposal_art and proposal_art.data:
            concepts = proposal_art.data.get("concepts", [])
            sel_id = proposal_art.data.get("selected_concept_id")
            if sel_id:
                selected_concept = next((c for c in concepts if c.get("concept_id") == sel_id), {})
            if not selected_concept and concepts:
                selected_concept = concepts[0]

        topic = str(
            state.metadata.get("topic")
            or script_data.get("title")
            or "AI Technology"
        )

        # 2. Build prompt
        prompt = build_scene_plan_prompt(
            topic=topic,
            script_data=script_data,
            selected_concept=selected_concept,
            art_direction_data=art_direction_data,
            research_brief_data=research_art.data if research_art else None,
        )

        # 3. Invoke LLM
        try:
            raw_plan, prov_name, model_name, tokens = self.llm_caller(
                prompt=prompt,
                system=SCENE_PLAN_SYSTEM_PROMPT,
            )
        except Exception as exc:
            return StageHandlerResult(
                status=StageResultStatus.FAILED,
                message=f"LLM scene plan generation failed: {exc}",
                errors=[str(exc)],
            )

        raw_scenes = raw_plan.get("scenes", [])
        if not isinstance(raw_scenes, list):
            raw_scenes = []

        # 4. Align raw scenes with script sections if needed
        # If LLM didn't produce 1 scene per section or missed sections, align them
        enriched_scenes: list[dict[str, Any]] = []
        sec_map = {
            (s.get("section_id") or s.get("id")): s
            for s in sections
        }

        # If LLM generated scenes, enrich them; if count doesn't match, map to script
        default_metaphor = art_direction_data.get("visual_metaphor") or selected_concept.get("visual_metaphor") or "Physical system dynamics"
        default_signature = art_direction_data.get("signature_device", "Dynamic telemetry trail")

        # Map scenes by section_id or index
        for idx, sec in enumerate(sections):
            sec_id = sec.get("section_id") or sec.get("id") or f"sec_{idx + 1:02d}"
            matching_raw = None
            for rs in raw_scenes:
                if rs.get("script_section_id") == sec_id:
                    matching_raw = rs
                    break
            if not matching_raw and idx < len(raw_scenes):
                matching_raw = raw_scenes[idx]

            start_t = sec.get("estimated_start") if sec.get("estimated_start") is not None else sec.get("timestamp_start", 0.0)
            end_t = sec.get("estimated_end") if sec.get("estimated_end") is not None else sec.get("timestamp_end", start_t + sec.get("duration", 3.0))
            duration = round(end_t - start_t, 2)

            sc_id = f"scene_{idx + 1:02d}"
            role = sec.get("narrative_role", "context")

            # Extract fields from LLM or provide strong editorial defaults
            if matching_raw:
                stype = matching_raw.get("type", "animation")
                if stype not in VALID_SCENE_TYPES:
                    stype = "animation" if role != "cta" else "text_card"

                visual_technique = matching_raw.get("visual_technique", "diagram_reveal")
                if visual_technique not in VALID_VISUAL_TECHNIQUES:
                    visual_technique = "diagram_reveal"

                cam_intent = matching_raw.get("camera_intent", "approach_subject")
                if cam_intent not in VALID_CAMERA_INTENTS:
                    cam_intent = "approach_subject"

                motion_intent = matching_raw.get("motion_intent", "assemble")
                if motion_intent not in VALID_MOTION_INTENTS:
                    motion_intent = "assemble"

                viewer_understanding = matching_raw.get("viewer_understanding") or f"Viewer observes the tangible operation of {sec.get('primary_subject', 'the system')}."
                visual_purpose = matching_raw.get("visual_purpose") or ("establish scale" if idx == 0 else "show mechanism")
                visual_metaphor = matching_raw.get("visual_metaphor") or default_metaphor
                subject = matching_raw.get("subject") or sec.get("primary_subject") or "Core Architecture"
                subject_action = matching_raw.get("subject_action") or f"Dynamic processing and scaling of {subject}"
                environment = matching_raw.get("environment") or "Industrial high-density technical space"
                composition = matching_raw.get("composition_intent") or matching_raw.get("composition") or "wide asymmetrical layout"
                continuity_prev = matching_raw.get("continuity_from_previous") or ("cold open" if idx == 0 else f"Camera tracks from scene {idx}")
                continuity_next = matching_raw.get("continuity_to_next") or ("concluding frame" if idx == len(sections) - 1 else f"Transition into scene {idx + 2}")
                req_assets = matching_raw.get("required_assets") or [
                    {"asset_type": "generated_video", "purpose": f"show {subject}", "visual_role": "primary"}
                ]
                raw_td = str(matching_raw.get("text_density", "low")).lower()
                text_density = raw_td if raw_td in ("low", "medium", "high") else "low"

                raw_sig = str(matching_raw.get("signature_device_usage", "")).lower()
                if raw_sig in ("key_beat", "key", "prominent", "hero", "primary", "high"):
                    sig_usage = "key_beat"
                elif raw_sig in ("subtle", "low", "medium", "accent"):
                    sig_usage = "subtle"
                else:
                    sig_usage = "none"
            else:
                # Fallback to editorial defaults
                stype = "diagram" if role == "mechanism" else ("broll" if role == "evidence" else ("text_card" if role == "cta" else "animation"))
                visual_technique = "diagram_reveal" if role == "mechanism" else ("evidence_wall" if role == "evidence" else ("kinetic_typography" if role == "cta" else "scale_transition"))
                cam_intent = "approach_subject"
                motion_intent = "assemble"
                viewer_understanding = f"Viewer clearly understands the {role} of {sec.get('primary_subject', topic)}."
                visual_purpose = "convert attention into subscription" if role == "cta" else ("establish scale" if idx == 0 else "show mechanism")
                visual_metaphor = default_metaphor
                subject = sec.get("primary_subject") or topic
                subject_action = f"Assembly and active progression of {subject}"
                environment = "Technical high-contrast lab"
                composition = "split-screen dynamic" if idx % 2 == 1 else "wide isometric"
                continuity_prev = "cold open" if idx == 0 else f"Direct continuation from scene {idx}"
                continuity_next = "final brand screen" if idx == len(sections) - 1 else f"Flows into scene {idx + 2}"
                req_assets = [{"asset_type": "generated_video", "purpose": f"visualize {subject}", "visual_role": "primary"}]
                text_density = "low"
                sig_usage = "key_beat" if idx == 1 else "none"

            # If CTA scene, force finality attributes
            if role == "cta":
                stype = "text_card"
                visual_technique = "kinetic_typography"
                viewer_understanding = "Viewer knows how to continue following the channel and subscribe."
                visual_purpose = "Convert attention into subscription."
                subject = "AI Simplified Lab Brand Identity"
                subject_action = "Pulsing subscription CTA cue and channel logo reveal"
                composition = "centered brand focus"

            # Generate shot beats covering full duration with zero gaps/overlaps
            shots = generate_scene_shots(
                scene_id=sc_id,
                duration=duration,
                subject=subject,
                visual_purpose=visual_purpose,
                camera_intent=cam_intent,
                motion_intent=motion_intent,
                visual_technique=visual_technique,
            )

            scene_obj: dict[str, Any] = {
                "id": sc_id,
                "scene_id": sc_id,
                "type": stype,
                "start_seconds": start_t,
                "end_seconds": end_t,
                "script_section_id": sec_id,
                "narrative_role": role,
                "information_role": sec.get("primary_intent", "explain"),
                "viewer_understanding": viewer_understanding,
                "visual_purpose": visual_purpose,
                "visual_metaphor": visual_metaphor,
                "subject": subject,
                "subject_action": subject_action,
                "environment": environment,
                "composition": composition,
                "composition_intent": composition,
                "spatial_relationships": "Foreground subject anchoring narrative with receding background context",
                "depth_strategy": "Layered foreground telemetry, middle subject, deep atmosphere",
                "camera_intent": cam_intent,
                "motion_intent": motion_intent,
                "transition_in": "cut" if idx == 0 else "smooth_zoom",
                "transition_out": "smooth_zoom" if idx < len(sections) - 1 else "fade_black",
                "transition_intent": "hard cut" if idx % 2 == 0 else "directional push",
                "visual_technique": visual_technique,
                "caption_intent": "synchronized kinetic phrase tracking",
                "continuity_from_previous": continuity_prev,
                "continuity_to_next": continuity_next,
                "variation_reason": f"Shifts from {sections[idx-1].get('narrative_role') if idx > 0 else 'start'} to {role}",
                "text_density": text_density,
                "signature_device_usage": sig_usage,
                "required_assets": req_assets,
                "shots": shots,
                "shot_intent": visual_purpose,  # For schema compatibility
            }
            enriched_scenes.append(scene_obj)

        total_duration = round(enriched_scenes[-1]["end_seconds"], 2) if enriched_scenes else 0.0

        # 4b. Reconcile variety to enforce diversity constraints
        _enforce_variety_reconciliation(enriched_scenes)

        # 5. Evaluate Variety via Variety Governor
        variety_rep = self.variety_governor.evaluate(
            enriched_scenes,
            art_direction=art_direction_data,
        )

        scene_plan_payload: dict[str, Any] = {
            "scenes": enriched_scenes,
            "total_duration_seconds": total_duration,
            "variety_score": variety_rep.variety_score,
            "scene_type_distribution": variety_rep.scene_type_distribution,
            "technique_usage": variety_rep.technique_usage,
        }

        # 6. Validate complete scene plan
        val_rep = self.validator.validate(
            scene_plan_data=scene_plan_payload,
            script_data=script_data,
            art_direction_data=art_direction_data,
        )

        if val_rep.status == "rejected":
            error_msgs = [f"[{f.code}] {f.message}" for f in val_rep.findings if f.severity == "critical"]
            return StageHandlerResult(
                status=StageResultStatus.FAILED,
                message="Scene plan failed validation: " + "; ".join(error_msgs),
                errors=error_msgs,
                warnings=[f.message for f in val_rep.findings if f.severity == "warning"],
            )

        warnings = [f.message for f in val_rep.findings if f.severity == "warning"]

        # 7. Provenance
        prompt_hash = f"sha256:{hashlib.sha256(prompt.encode('utf-8')).hexdigest()}"
        est_cost = round(tokens * 0.000001, 6)

        producer = ProducerInfo(
            kind=ProducerKind.LLM,
            provider=prov_name,
            model=model_name,
            prompt_hash=prompt_hash,
            estimated_cost=est_cost,
        )

        return StageHandlerResult(
            status=StageResultStatus.READY,
            data=scene_plan_payload,
            producer=producer,
            warnings=warnings,
            message=(
                f"Scene plan generated: {len(enriched_scenes)} scenes, "
                f"variety score {variety_rep.variety_score}/100, duration {total_duration:.1f}s."
            ),
        )
