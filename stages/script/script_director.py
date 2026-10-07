"""Script Director — synthesizes, times, and validates spoken-word scripts.

Implements StageHandler for the 'script' stage.
Consumes:
- research_brief
- proposal_packet
- art_direction (optional if available)
Produces:
- script artifact with deterministic timing, voice performance, and entity separation.
"""
from __future__ import annotations

import hashlib
from typing import Any

import models
from schemas.models.artifact import ArtifactEnvelope, ProducerInfo
from schemas.models.common import ProducerKind
from schemas.models.production import ProductionState
from production.stage_registry import StageHandler, StageHandlerResult, StageResultStatus
from stages.script.intent_classifier import classify_intent, extract_entities_and_emphasis
from stages.script.script_prompts import SCRIPT_SYSTEM_PROMPT, build_script_prompt
from stages.script.script_validator import ScriptValidator
from stages.script.timing import apply_script_timing
from stages.script.voice_performance import determine_voice_performance, format_speaker_direction

DEFAULT_CTA_TEXT = "Subscribe to AI Simplified Lab for more AI breakdowns like this."


class ScriptHandler:
    """Production stage handler for high-retention video script generation."""

    def __init__(
        self,
        llm_caller: Any | None = None,
        target_duration: float = 45.0,
        min_duration: float = 30.0,
        max_duration: float = 60.0,
    ) -> None:
        self.llm_caller = llm_caller or models.call_llm_json
        self.target_duration = target_duration
        self.validator = ScriptValidator(
            min_duration=min_duration,
            max_duration=max_duration,
        )

    def run(
        self,
        stage_name: str,
        state: ProductionState,
        inputs: dict[str, ArtifactEnvelope],
        **kwargs: Any,
    ) -> StageHandlerResult:
        # 1. Validate upstream inputs
        research_art = inputs.get("research_brief")
        if not research_art or not research_art.data:
            return StageHandlerResult(
                status=StageResultStatus.BLOCKED,
                message="Script stage blocked: missing required 'research_brief' artifact.",
                errors=["MISSING_UPSTREAM_RESEARCH_BRIEF"],
            )

        proposal_art = inputs.get("proposal_packet")
        if not proposal_art or not proposal_art.data:
            return StageHandlerResult(
                status=StageResultStatus.BLOCKED,
                message="Script stage blocked: missing required 'proposal_packet' artifact.",
                errors=["MISSING_UPSTREAM_PROPOSAL_PACKET"],
            )

        # Optional art direction
        art_direction_art = inputs.get("art_direction")
        art_direction_data = art_direction_art.data if art_direction_art else None

        # Resolve selected concept
        proposal_data = proposal_art.data
        concepts = proposal_data.get("concepts", [])
        selected_id = proposal_data.get("selected_concept_id")
        if not selected_id and concepts:
            selected_id = concepts[0].get("concept_id")

        selected_concept = next((c for c in concepts if c.get("concept_id") == selected_id), None)
        if not selected_concept and concepts:
            selected_concept = concepts[0]
        elif not selected_concept:
            return StageHandlerResult(
                status=StageResultStatus.BLOCKED,
                message="Script stage blocked: no concepts found in proposal packet.",
                errors=["NO_PROPOSAL_CONCEPTS"],
            )

        topic = str(state.metadata.get("topic") or research_art.data.get("topic") or "AI Technology")
        target_dur = float(
            kwargs.get("target_duration")
            or selected_concept.get("target_duration")
            or self.target_duration
        )

        # 2. Build prompt
        prompt = build_script_prompt(
            topic=topic,
            research_brief=research_art.data,
            selected_concept=selected_concept,
            art_direction=art_direction_data,
            target_duration=target_dur,
        )

        # 3. Invoke LLM
        try:
            raw_script, prov_name, model_name, tokens = self.llm_caller(
                prompt=prompt,
                system=SCRIPT_SYSTEM_PROMPT,
            )
        except Exception as exc:
            return StageHandlerResult(
                status=StageResultStatus.FAILED,
                message=f"LLM script generation failed: {exc}",
                errors=[str(exc)],
            )

        # 4. Normalize and enrich sections
        sections = raw_script.get("sections", [])
        if not isinstance(sections, list):
            sections = []

        # Ensure CTA section exists at the end
        has_cta = any(s.get("narrative_role") == "cta" for s in sections)
        if not has_cta:
            sections.append({
                "section_id": f"sec_{len(sections) + 1:02d}",
                "narrative_role": "cta",
                "spoken_text": DEFAULT_CTA_TEXT,
                "visual_intent": "Clean brand signature sequence with dynamic subscriber trigger.",
                "pause_after": 0.3,
            })
        elif sections[-1].get("narrative_role") != "cta":
            # If CTA is not the last section, move it to the end
            cta_idx = next(i for i, s in enumerate(sections) if s.get("narrative_role") == "cta")
            cta_sec = sections.pop(cta_idx)
            sections.append(cta_sec)

        # Process each section: intents, entities, voice performance
        for idx, sec in enumerate(sections):
            sec_id = sec.get("section_id") or sec.get("id") or f"sec_{idx + 1:02d}"
            sec["id"] = sec_id
            sec["section_id"] = sec_id

            spoken = sec.get("spoken_text", "")
            role = sec.get("narrative_role", "context")

            # Intent classification (strictly 1 primary, max 2 secondaries)
            primary_intent, secondary_intents = classify_intent(
                narrative_role=role,
                spoken_text=spoken,
                explicit_primary=sec.get("primary_intent"),
                explicit_secondary=sec.get("secondary_intents"),
            )
            sec["primary_intent"] = primary_intent
            sec["secondary_intents"] = secondary_intents

            # Entity extraction (strictly separate entities and emphasis words)
            extracted = extract_entities_and_emphasis(
                spoken_text=spoken,
                primary_subject_hint=sec.get("primary_subject", ""),
                emphasis_hint=sec.get("emphasis_words") or sec.get("emphasis_cues"),
                entities_hint=sec.get("entities"),
                keywords_hint=sec.get("keywords"),
            )
            sec["primary_subject"] = extracted.primary_subject
            sec["entities"] = extracted.entities
            sec["keywords"] = extracted.keywords
            sec["emphasis_words"] = extracted.emphasis_words
            sec["emphasis_cues"] = extracted.emphasis_words

            # Voice performance
            perf = determine_voice_performance(
                narrative_role=role,
                override_dict=sec.get("performance_direction"),
            )
            sec["performance_direction"] = perf
            sec["speaker_direction"] = format_speaker_direction(perf)

        # 5. Deterministic Timing Engine
        timed_sections, total_duration, total_words = apply_script_timing(
            sections=sections,
            target_duration=target_dur,
        )

        title = raw_script.get("title") or selected_concept.get("title") or topic
        hook_text = raw_script.get("hook") or (timed_sections[0].get("spoken_text") if timed_sections else "")
        vo_script_text = " ".join(s.get("spoken_text", "") for s in timed_sections)

        cta_sec = timed_sections[-1]
        cta_obj = {
            "section_id": cta_sec.get("section_id", "sec_cta"),
            "narrative_role": "cta",
            "spoken_text": cta_sec.get("spoken_text", DEFAULT_CTA_TEXT),
            "duration": cta_sec.get("duration", 3.5),
            "visual_intent": cta_sec.get("visual_intent", "Channel brand card"),
        }

        prod_id = getattr(state, "project_id", getattr(state, "production_id", "prod_default"))
        script_payload: dict[str, Any] = {
            "production_id": prod_id,
            "title": title,
            "hook": hook_text,
            "audience": raw_script.get("audience", "AI Enthusiasts and Engineers"),
            "target_duration": target_dur,
            "target_duration_seconds": target_dur,
            "estimated_duration": total_duration,
            "estimated_duration_seconds": total_duration,
            "word_count": total_words,
            "spoken_word_count": total_words,
            "timing_status": "valid",
            "cta": cta_obj,
            "sections": timed_sections,
            "vo_script_text": vo_script_text,
        }

        # 6. Validate script artifact
        report = self.validator.validate(script_payload)
        if report.status == "rejected":
            error_msgs = [f"[{f.code}] {f.message}" for f in report.findings if f.severity == "critical"]
            return StageHandlerResult(
                status=StageResultStatus.FAILED,
                message="Script failed validation: " + "; ".join(error_msgs),
                errors=error_msgs,
                warnings=[f.message for f in report.findings if f.severity == "warning"],
            )

        warnings = [f.message for f in report.findings if f.severity == "warning"]

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
            data=script_payload,
            producer=producer,
            warnings=warnings,
            message=(
                f"Script generated: {len(timed_sections)} sections, "
                f"{total_words} words, estimated duration {total_duration:.1f}s."
            ),
        )
