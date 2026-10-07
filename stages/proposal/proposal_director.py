"""Proposal Director — generates, validates, and manages concept selection and runtime locking.

Implements StageHandler for the 'proposal' stage.
Consumes research_brief artifact and generates 3 materially divergent concepts.
Locks renderer_family, render_runtime, and composition_mode once a concept is selected.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any

import models
from schemas.models.artifact import ArtifactEnvelope, ProducerInfo
from schemas.models.common import ProducerKind, RunMode
from schemas.models.production import ProductionState
from production.stage_registry import StageHandler, StageHandlerResult, StageResultStatus
from stages.proposal.proposal_prompts import PROPOSAL_SYSTEM_PROMPT, build_proposal_prompt
from stages.proposal.proposal_validator import ProposalValidator


class ProposalHandler:
    """Production stage handler for creative proposal generation."""

    def __init__(
        self,
        llm_caller: Any | None = None,
        min_diversity_score: float = 65.0,
    ) -> None:
        self.llm_caller = llm_caller or models.call_llm_json
        self.validator = ProposalValidator(min_diversity_score=min_diversity_score)

    def run(
        self,
        stage_name: str,
        state: ProductionState,
        inputs: dict[str, ArtifactEnvelope],
        **kwargs: Any,
    ) -> StageHandlerResult:
        research_brief_art = inputs.get("research_brief")
        if not research_brief_art or not research_brief_art.data:
            return StageHandlerResult(
                status=StageResultStatus.BLOCKED,
                message="Proposal stage blocked: missing required upstream artifact 'research_brief'.",
                errors=["MISSING_UPSTREAM_RESEARCH_BRIEF"],
            )

        research_data = research_brief_art.data
        target_duration = float(state.target_duration or 35.0)
        platform = str(state.platform or "youtube_shorts")

        # 1. Prompt LLM to generate 3 divergent concepts
        prompt = build_proposal_prompt(
            research_brief_data=research_data,
            target_duration=target_duration,
            platform=platform,
        )

        try:
            parsed_data, prov_name, model_name, tokens = self.llm_caller(
                prompt=prompt,
                system=PROPOSAL_SYSTEM_PROMPT,
            )
        except Exception as exc:
            return StageHandlerResult(
                status=StageResultStatus.FAILED,
                message=f"LLM proposal concept generation failed: {exc}",
                errors=[str(exc)],
            )

        concepts = parsed_data.get("concepts", [])

        # Ensure concept_id format
        for idx, c in enumerate(concepts, 1):
            if "concept_id" not in c or not c["concept_id"]:
                c["concept_id"] = f"concept_{idx:02d}"

        # 2. Validate concepts and check diversity score
        val_report = self.validator.validate(parsed_data, research_data=research_data)

        if val_report.status == "rejected":
            error_msgs = [f"[{f.code}] {f.message}" for f in val_report.findings if f.severity == "critical"]
            return StageHandlerResult(
                status=StageResultStatus.FAILED,
                message="Proposal concepts failed validation: " + "; ".join(error_msgs),
                errors=error_msgs,
                warnings=[f.message for f in val_report.findings if f.severity == "warning"],
            )

        warnings = [f.message for f in val_report.findings if f.severity == "warning"]

        # 3. Selection & Runtime Locking
        selected_id = kwargs.get("selected_concept_id") or parsed_data.get("selected_concept_id")
        is_auto_mode = (state.run_mode == RunMode.AUTO)

        if not selected_id and is_auto_mode:
            # AUTO mode: select the first valid concept
            selected_id = concepts[0]["concept_id"]

        decision_log = None
        if selected_id:
            selected_concept = next((c for c in concepts if c["concept_id"] == selected_id), None)
            if not selected_concept:
                return StageHandlerResult(
                    status=StageResultStatus.FAILED,
                    message=f"Selected concept {selected_id!r} not found in generated concepts.",
                    errors=[f"Concept {selected_id} not in concepts"],
                )

            rejected_ids = [c["concept_id"] for c in concepts if c["concept_id"] != selected_id]
            actor = "human" if not is_auto_mode else "system"
            selection_mode = "manual" if not is_auto_mode else "auto"

            locked_decisions = {
                "renderer_family": selected_concept.get("renderer_family"),
                "render_runtime": selected_concept.get("render_runtime"),
                "composition_mode": selected_concept.get("composition_mode"),
            }

            decision_log = {
                "selected_concept_id": selected_id,
                "decision_reason": f"Concept '{selected_concept.get('title')}' chosen with metaphor: {selected_concept.get('visual_metaphor')!r}",
                "selection_mode": selection_mode,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "actor": actor,
                "rejected_concepts": rejected_ids,
                "locked_decisions": locked_decisions,
            }

            parsed_data["selected_concept_id"] = selected_id
            parsed_data["decision_log"] = decision_log

            # Lock decisions in state metadata and audit decisions
            state.add_decision(
                stage="proposal",
                decision=f"Selected {selected_id} ({selected_concept.get('title')})",
                reason=f"Runtime locked: {locked_decisions}",
                actor=actor,
            )
            state.metadata["locked_runtime"] = locked_decisions
            state.metadata["selected_concept"] = selected_concept
        else:
            parsed_data["selected_concept_id"] = None
            parsed_data["decision_log"] = None

        # 4. Provenance
        prompt_hash = f"sha256:{hashlib.sha256(prompt.encode('utf-8')).hexdigest()}"
        est_cost = round(tokens * 0.000001, 6)
        producer = ProducerInfo(
            kind=ProducerKind.LLM,
            provider=prov_name,
            model=model_name,
            prompt_hash=prompt_hash,
            estimated_cost=est_cost,
        )

        final_status = (
            StageResultStatus.READY
            if is_auto_mode and selected_id
            else StageResultStatus.WAITING_APPROVAL
        )

        return StageHandlerResult(
            status=final_status,
            data=parsed_data,
            producer=producer,
            warnings=warnings,
            message=(
                f"Generated {len(concepts)} concepts (diversity score: {val_report.concept_diversity_score:.1f}/100). "
                f"Selection: {selected_id or 'pending approval'}."
            ),
        )
