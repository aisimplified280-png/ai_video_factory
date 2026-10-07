"""Art Direction Director — generates, validates, and manages creative art direction.

Implements StageHandler for the 'art_direction' stage.
Consumes proposal_packet (and optional script if present).
Produces concrete art_direction artifact with visual metaphor, dials, anti-patterns,
and signature device.
"""
from __future__ import annotations

import hashlib
from typing import Any

import models
from schemas.models.artifact import ArtifactEnvelope, ProducerInfo
from schemas.models.common import ProducerKind
from schemas.models.production import ProductionState
from production.stage_registry import StageHandler, StageHandlerResult, StageResultStatus
from stages.art_direction.art_direction_prompts import ART_DIRECTION_SYSTEM_PROMPT, build_art_direction_prompt
from stages.art_direction.art_direction_validator import ArtDirectionValidator


class ArtDirectionHandler:
    """Production stage handler for creative art direction."""

    def __init__(
        self,
        llm_caller: Any | None = None,
        default_visual_variance: int = 8,
        default_motion_intensity: int = 6,
        default_information_density: int = 5,
    ) -> None:
        self.llm_caller = llm_caller or models.call_llm_json
        self.validator = ArtDirectionValidator()
        self.default_visual_variance = default_visual_variance
        self.default_motion_intensity = default_motion_intensity
        self.default_information_density = default_information_density

    def run(
        self,
        stage_name: str,
        state: ProductionState,
        inputs: dict[str, ArtifactEnvelope],
        **kwargs: Any,
    ) -> StageHandlerResult:
        proposal_art = inputs.get("proposal_packet")
        if not proposal_art or not proposal_art.data:
            return StageHandlerResult(
                status=StageResultStatus.BLOCKED,
                message="Art direction blocked: missing upstream 'proposal_packet' artifact.",
                errors=["MISSING_UPSTREAM_PROPOSAL_PACKET"],
            )

        proposal_data = proposal_art.data
        concepts = proposal_data.get("concepts", [])
        selected_id = proposal_data.get("selected_concept_id")

        if not selected_id and concepts:
            # Fall back to first concept if approved
            selected_id = concepts[0].get("concept_id")

        selected_concept = next((c for c in concepts if c.get("concept_id") == selected_id), None)
        if not selected_concept:
            return StageHandlerResult(
                status=StageResultStatus.BLOCKED,
                message=f"Art direction blocked: selected concept {selected_id!r} not found in proposal concepts.",
                errors=["NO_SELECTED_CONCEPT"],
            )

        # Optional script if available (never fabricate)
        script_art = inputs.get("script")
        script_data = script_art.data if script_art else None

        topic = str(state.metadata.get("topic") or "AI Technology")

        # 1. Build prompt
        prompt = build_art_direction_prompt(
            concept=selected_concept,
            topic=topic,
            script_data=script_data,
        )

        # 2. Invoke LLM
        try:
            parsed_data, prov_name, model_name, tokens = self.llm_caller(
                prompt=prompt,
                system=ART_DIRECTION_SYSTEM_PROMPT,
            )
        except Exception as exc:
            return StageHandlerResult(
                status=StageResultStatus.FAILED,
                message=f"LLM art direction generation failed: {exc}",
                errors=[str(exc)],
            )

        # 3. Apply default dials and ensure clamped 1-10 integers
        parsed_data["visual_variance"] = int(
            max(1, min(10, parsed_data.get("visual_variance", self.default_visual_variance)))
        )
        parsed_data["motion_intensity"] = int(
            max(1, min(10, parsed_data.get("motion_intensity", self.default_motion_intensity)))
        )
        parsed_data["information_density"] = int(
            max(1, min(10, parsed_data.get("information_density", self.default_information_density)))
        )

        # Inherit visual metaphor from concept if not provided
        if not parsed_data.get("visual_metaphor"):
            parsed_data["visual_metaphor"] = selected_concept.get("visual_metaphor", "")

        # 4. Validate art direction
        val_report = self.validator.validate(parsed_data)
        if val_report.status == "rejected":
            error_msgs = [f"[{f.code}] {f.message}" for f in val_report.findings if f.severity == "critical"]
            return StageHandlerResult(
                status=StageResultStatus.FAILED,
                message="Art direction failed validation: " + "; ".join(error_msgs),
                errors=error_msgs,
                warnings=[f.message for f in val_report.findings if f.severity == "warning"],
            )

        warnings = [f.message for f in val_report.findings if f.severity == "warning"]

        # 5. Provenance
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
            data=parsed_data,
            producer=producer,
            warnings=warnings,
            message=(
                f"Art direction established. Metaphor: {parsed_data['visual_metaphor']!r}, "
                f"Dials: (variance={parsed_data['visual_variance']}, "
                f"motion={parsed_data['motion_intensity']}, density={parsed_data['information_density']})."
            ),
        )
