"""StageRunner — orchestrates a single stage execution lifecycle.

Enforces:
- Pre-execution runnability checks (dependencies, revision limit, budget)
- Explicit dependency locking (recording exact parent artifact versions & hashes)
- Handler delegation via StageRegistry
- Quality gate evaluations on stage output
- Atomic artifact creation and persistence via ArtifactStore
- Explicit StageResult reporting without unhandled exceptions
"""
from __future__ import annotations

import uuid
from typing import Any
from pydantic import BaseModel, Field

from schemas.models.artifact import ArtifactEnvelope, ArtifactReference, ProducerInfo
from schemas.models.common import ArtifactStatus, ApprovalMode, ProductionStatus, QualityGateType
from schemas.models.pipeline import PipelineDefinition, StageDefinition, QualityGate
from schemas.models.production import ProductionState
from production.artifact_store import ArtifactStore, ArtifactStoreError
from production.dependencies import resolve_dependencies
from production.stage_registry import (
    StageHandler,
    StageHandlerResult,
    StageRegistry,
    StageResultStatus,
    global_stage_registry,
    default_production_registry,
)


class StageResult(BaseModel):
    """The formal, typed result of a StageRunner execution."""
    status: StageResultStatus
    stage: str
    artifact_type: str | None = None
    artifact_version: int | None = None
    content_hash: str | None = None
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    execution_id: str = Field(default_factory=lambda: f"exec_{uuid.uuid4().hex[:12]}")
    message: str = ""

    model_config = {"extra": "forbid"}


class StageRunner:
    """Orchestrates the lifecycle of one stage execution."""

    def __init__(
        self,
        artifact_store: ArtifactStore,
        registry: StageRegistry | None = None,
    ) -> None:
        self.artifact_store = artifact_store
        self.registry = registry if registry is not None else default_production_registry

    def run(
        self,
        stage_name: str,
        pipeline_def: PipelineDefinition,
        state: ProductionState,
        notes: str = "",
        **kwargs: Any,
    ) -> StageResult:
        """Execute a stage lifecycle and return a typed StageResult."""
        # 1. State check: is production aborted?
        if state.status == ProductionStatus.ABORTED:
            return StageResult(
                status=StageResultStatus.BLOCKED,
                stage=stage_name,
                message=f"Production {state.project_id!r} is aborted. Cannot run stage {stage_name!r}.",
            )

        # 2. Stage check: does it exist in the pipeline?
        stage_def = pipeline_def.get_stage(stage_name)
        if stage_def is None:
            return StageResult(
                status=StageResultStatus.BLOCKED,
                stage=stage_name,
                message=f"Stage {stage_name!r} not defined in pipeline {pipeline_def.name!r}.",
            )

        # 3. Revision limit check
        current_revisions = state.get_revision_count(stage_name)
        if current_revisions >= stage_def.max_revisions:
            return StageResult(
                status=StageResultStatus.BLOCKED,
                stage=stage_name,
                message=(
                    f"Stage {stage_name!r} reached maximum revisions "
                    f"({current_revisions}/{stage_def.max_revisions})."
                ),
            )

        # 4. Budget check
        if state.budget.is_over_budget:
            return StageResult(
                status=StageResultStatus.BLOCKED,
                stage=stage_name,
                message=(
                    f"Production is over budget cap (${state.budget.budget_cap:.2f}, "
                    f"spent: ${state.budget.actual_cost:.2f})."
                ),
            )

        # 5. Dependency resolution & locking
        locked_refs, blockers = resolve_dependencies(
            stage_name, pipeline_def, state, self.artifact_store
        )
        if blockers:
            return StageResult(
                status=StageResultStatus.BLOCKED,
                stage=stage_name,
                message=f"Stage {stage_name!r} blocked: " + "; ".join(blockers),
                errors=blockers,
            )

        # 6. Check handler registration
        handler = self.registry.get(stage_name)
        if handler is None:
            return StageResult(
                status=StageResultStatus.NOT_IMPLEMENTED,
                stage=stage_name,
                message=(
                    f"Stage {stage_name!r} is not yet implemented (scheduled for future phase). "
                    f"No handler registered in StageRegistry."
                ),
            )

        # 7. Load inputs for handler
        inputs: dict[str, ArtifactEnvelope] = {}
        for ref in locked_refs:
            if ref.artifact_type != "brief":
                try:
                    inputs[ref.artifact_type] = self.artifact_store.load(
                        ref.artifact_type, state.project_id, version=ref.version
                    )
                except Exception as exc:
                    return StageResult(
                        status=StageResultStatus.FAILED,
                        stage=stage_name,
                        message=f"Failed loading input {ref.artifact_type} v{ref.version}: {exc}",
                        errors=[str(exc)],
                    )

        # 8. Execute handler
        try:
            handler_result = handler.run(stage_name, state, inputs, notes=notes, **kwargs)
        except Exception as exc:
            return StageResult(
                status=StageResultStatus.FAILED,
                stage=stage_name,
                message=f"Handler for stage {stage_name!r} raised unhandled exception: {exc}",
                errors=[str(exc)],
            )

        # If handler returned failure / blocked / not_implemented, forward immediately
        if handler_result.status != StageResultStatus.READY and handler_result.status != StageResultStatus.WAITING_APPROVAL:
            return StageResult(
                status=handler_result.status,
                stage=stage_name,
                warnings=handler_result.warnings,
                errors=handler_result.errors,
                message=handler_result.message or f"Handler returned status {handler_result.status.value}",
            )

        if not handler_result.data:
            return StageResult(
                status=StageResultStatus.FAILED,
                stage=stage_name,
                message=f"Handler for stage {stage_name!r} returned no artifact data payload.",
                errors=["Empty artifact data payload"],
            )

        # 9. Evaluate stage quality gates
        gate_warnings, gate_errors = self._evaluate_quality_gates(
            stage_def.quality_gates, handler_result.data
        )
        if gate_errors:
            return StageResult(
                status=StageResultStatus.FAILED,
                stage=stage_name,
                warnings=handler_result.warnings + gate_warnings,
                errors=handler_result.errors + gate_errors,
                message=f"Quality gate failure in stage {stage_name!r}: " + "; ".join(gate_errors),
            )

        # 10. Create and persist artifact
        produced_type = stage_def.produces[0] if stage_def.produces else f"{stage_name}_artifact"
        effective_app_mode = pipeline_def.effective_approval(stage_name, state.run_mode)

        try:
            envelope = self.artifact_store.create(
                artifact_type=produced_type,
                production_id=state.project_id,
                stage=stage_name,
                data=handler_result.data,
                producer=handler_result.producer,
                parent_artifacts=locked_refs,
                warnings=handler_result.warnings + gate_warnings,
            )

            # Set status: ready or pending
            if effective_app_mode == ApprovalMode.AUTO:
                envelope.status = ArtifactStatus.READY
            else:
                envelope.status = ArtifactStatus.PENDING

            artifact_path = self.artifact_store.save(envelope)
            # Phase 6 keeps review/benchmark reports beside the canonical edit artifact.
            # They are derived views; only edit_decisions is an authoritative artifact.
            if stage_name == "edit":
                from stages.edit.edit_director import EditDirector
                EditDirector.write_human_reports(artifact_path.parent, handler_result.data)
        except ArtifactStoreError as exc:
            return StageResult(
                status=StageResultStatus.FAILED,
                stage=stage_name,
                message=f"Failed to persist artifact for stage {stage_name!r}: {exc}",
                errors=[str(exc)],
            )

        # Update active artifact version in state
        state.set_active_version(envelope.artifact_type, envelope.artifact_version)

        final_status = (
            StageResultStatus.WAITING_APPROVAL
            if effective_app_mode == ApprovalMode.HUMAN
            else StageResultStatus.READY
        )

        return StageResult(
            status=final_status,
            stage=stage_name,
            artifact_type=envelope.artifact_type,
            artifact_version=envelope.artifact_version,
            content_hash=envelope.content_hash,
            warnings=handler_result.warnings + gate_warnings,
            message=f"Stage {stage_name!r} successfully produced {produced_type} v{envelope.artifact_version}",
        )

    @staticmethod
    def _evaluate_quality_gates(
        gates: list[QualityGate],
        data: dict[str, Any],
    ) -> tuple[list[str], list[str]]:
        """Evaluate quality gates against artifact data payload.

        Returns (warnings, errors).
        """
        warnings: list[str] = []
        errors: list[str] = []

        for gate in gates:
            val = data.get(gate.field)
            passed = True
            reason = ""

            if gate.type == QualityGateType.PRESENCE:
                if val is None or val == "" or val == [] or val == {}:
                    passed = False
                    reason = f"Field {gate.field!r} is missing or empty"

            elif gate.type == QualityGateType.MIN:
                if val is None:
                    passed = False
                    reason = f"Field {gate.field!r} is missing"
                else:
                    try:
                        num = len(val) if isinstance(val, (list, dict, str)) else float(val)
                        if gate.threshold is not None and num < gate.threshold:
                            passed = False
                            reason = f"Field {gate.field!r} value/count {num} < minimum threshold {gate.threshold}"
                    except (ValueError, TypeError):
                        passed = False
                        reason = f"Field {gate.field!r} cannot be compared to threshold"

            elif gate.type == QualityGateType.MAX:
                if val is not None:
                    try:
                        num = len(val) if isinstance(val, (list, dict, str)) else float(val)
                        if gate.threshold is not None and num > gate.threshold:
                            passed = False
                            reason = f"Field {gate.field!r} value/count {num} > maximum threshold {gate.threshold}"
                    except (ValueError, TypeError):
                        passed = False
                        reason = f"Field {gate.field!r} cannot be compared to threshold"

            elif gate.type == QualityGateType.BOOL:
                if bool(val) is not True:
                    passed = False
                    reason = f"Field {gate.field!r} is not True"

            if not passed:
                msg = f"Gate {gate.name!r} failed: {reason}"
                if gate.message:
                    msg += f" ({gate.message})"
                if gate.required:
                    errors.append(msg)
                else:
                    warnings.append(msg)

        return warnings, errors
