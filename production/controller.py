"""ProductionController — the central orchestrator for the video production system.

Orchestrates:
  - PipelineLoader & PipelineValidator
  - StateStore (ProductionState persistence)
  - ArtifactStore (Artifact persistence & immutability)
  - StageRunner (Stage execution lifecycle)
  - CheckpointStore (Crash recovery snapshots)
  - AuditLog (Chronological event logging)

The controller ONLY orchestrates. It does NOT contain stage logic or render implementations.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from schemas.models.common import (
    ApprovalMode,
    ArtifactStatus,
    ProductionStatus,
    RunMode,
    Severity,
)
from schemas.models.pipeline import PipelineDefinition
from schemas.models.production import ProductionState
from production.artifact_store import ArtifactStore, ArtifactStoreError
from production.audit import AuditLog
from production.checkpoint import CheckpointStore
from production.dependencies import invalidate_downstream, find_stale_artifacts
from production.pipeline_loader import PipelineLoader, PipelineNotFoundError
from production.pipeline_validator import PipelineValidator
from production.stage_registry import StageRegistry, StageResultStatus
from production.stage_runner import StageResult, StageRunner
from production.state import StateStore, ProductionNotFoundError, ProductionStateError


class ControllerError(Exception):
    """Base error for ProductionController operations."""


class ProductionAbortedError(ControllerError):
    """Raised when attempting to run an aborted production."""


class ProductionController:
    """Stateful orchestrator coordinating production runs from creation to completion."""

    def __init__(
        self,
        projects_root: Path | str = "output",
        pipeline_dir: Path | str | None = None,
        registry: StageRegistry | None = None,
    ) -> None:
        self.projects_root = Path(projects_root)
        self.pipeline_loader = PipelineLoader(
            pipeline_dir=Path(pipeline_dir) if pipeline_dir else None
        )
        self.pipeline_validator = PipelineValidator()
        self.state_store = StateStore(projects_root=self.projects_root)
        self.artifact_store = ArtifactStore(projects_root=self.projects_root)
        self.stage_runner = StageRunner(artifact_store=self.artifact_store, registry=registry)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_project_dir(self, production_id: str) -> Path:
        return self.projects_root / production_id

    def _get_audit_log(self, production_id: str) -> AuditLog:
        return AuditLog(self._get_project_dir(production_id), production_id)

    def _get_checkpoint_store(self, production_id: str) -> CheckpointStore:
        return CheckpointStore(self._get_project_dir(production_id), production_id)

    def _get_pipeline(self, pipeline_name: str) -> PipelineDefinition:
        defn = self.pipeline_loader.load(pipeline_name)
        errors = self.pipeline_validator.validate(defn)
        if errors:
            raise ControllerError(
                f"Pipeline {pipeline_name!r} failed validation:\n" + "\n".join(f"  - {e}" for e in errors)
            )
        return defn

    def _determine_next_stage(
        self,
        defn: PipelineDefinition,
        state: ProductionState,
    ) -> str | None:
        """Determine what stage should be executed next based on pipeline topology."""
        all_stages = defn.all_stage_names()
        for sname in all_stages:
            stage_def = defn.stages[sname]
            # If stage produces an artifact that is not yet active/approved, this is next
            produced_type = stage_def.produces[0] if stage_def.produces else None
            if produced_type:
                active_ver = state.get_active_version(produced_type)
                if active_ver is None:
                    return sname
                # If active version exists, verify its status in store
                try:
                    art = self.artifact_store.load(produced_type, state.project_id, version=active_ver)
                    if art.status != ArtifactStatus.APPROVED and art.status != ArtifactStatus.READY:
                        return sname
                except Exception:
                    return sname
        return None

    def _check_and_mark_completion(
        self,
        defn: PipelineDefinition,
        state: ProductionState,
    ) -> bool:
        """If all required stages have approved/ready artifacts, mark completed."""
        for req_stage in defn.required_stages:
            stage_def = defn.stages[req_stage]
            for prod_type in stage_def.produces:
                active_ver = state.get_active_version(prod_type)
                if active_ver is None:
                    return False
                try:
                    art = self.artifact_store.load(prod_type, state.project_id, version=active_ver)
                    if art.status not in (ArtifactStatus.APPROVED, ArtifactStatus.READY):
                        return False
                except Exception:
                    return False

        # All required stages produced valid artifacts
        state.status = ProductionStatus.COMPLETED
        state.current_stage = None
        self.state_store.save(state)
        self._get_checkpoint_store(state.project_id).create_checkpoint(
            state, "production_completed", message="All required pipeline stages completed successfully"
        )
        self._get_audit_log(state.project_id).record(
            "production_completed", message="Production marked completed"
        )
        return True

    # ------------------------------------------------------------------
    # Public Controller API
    # ------------------------------------------------------------------

    def start(
        self,
        topic: str,
        pipeline: str = "youtube-short",
        options: dict[str, Any] | None = None,
    ) -> ProductionState:
        """Create a new production run, initialize seed brief, state, checkpoint, and audit log."""
        options = options or {}
        defn = self._get_pipeline(pipeline)

        project_id = options.get("project_id") or f"proj_{uuid.uuid4().hex[:8]}"
        target_duration = float(options.get("target_duration") or defn.target_duration)
        aspect_ratio = str(options.get("aspect_ratio") or "9:16")
        platform = str(options.get("platform") or defn.platform)
        run_mode = RunMode(options.get("run_mode") or defn.run_mode_default.value)
        budget_cap = float(options.get("budget_cap") or defn.budget_policy.budget_cap)

        first_stage = defn.required_stages[0] if defn.required_stages else "research"

        # 1. Create initial state
        metadata = dict(options.get("metadata") or {})
        metadata["topic"] = topic

        state = self.state_store.create(
            project_id=project_id,
            pipeline=pipeline,
            pipeline_version=defn.version,
            target_duration=target_duration,
            aspect_ratio=aspect_ratio,
            platform=platform,
            style=str(options.get("style") or "auto"),
            run_mode=run_mode,
            budget_cap=budget_cap,
            metadata=metadata,
        )
        state.current_stage = first_stage
        self.state_store.save(state)

        # 2. Write seed brief artifact to brief/brief.json
        project_dir = self._get_project_dir(project_id)
        brief_dir = project_dir / "brief"
        brief_dir.mkdir(parents=True, exist_ok=True)
        brief_data = {
            "topic": topic,
            "target_duration": target_duration,
            "platform": platform,
            "aspect_ratio": aspect_ratio,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "options": options,
        }
        (brief_dir / "brief.json").write_text(json.dumps(brief_data, indent=2), encoding="utf-8")

        # 3. Checkpoint & audit log
        chk_store = self._get_checkpoint_store(project_id)
        chk_store.create_checkpoint(
            state, "production_created", stage=first_stage, message=f"Created production for topic: {topic!r}"
        )
        audit = self._get_audit_log(project_id)
        audit.record(
            "production_created",
            stage=first_stage,
            details={"pipeline": pipeline, "topic": topic, "budget_cap": budget_cap},
            message=f"Production {project_id} started with pipeline {pipeline}",
        )

        return state

    def resume(self, project_id: str) -> ProductionState:
        """Resume a production from disk after an interruption or crash."""
        state = self.state_store.load(project_id)
        if state.status == ProductionStatus.ABORTED:
            raise ProductionAbortedError(
                f"Production {project_id!r} is aborted and cannot be resumed."
            )

        defn = self._get_pipeline(state.pipeline)

        # Check for any stale downstream artifacts and invalidate them
        stale_map = find_stale_artifacts(state, self.artifact_store)
        if stale_map:
            for art_type in list(stale_map.keys()):
                if art_type in state.active_artifact_versions:
                    del state.active_artifact_versions[art_type]

        # Determine the next runnable / uncompleted stage
        next_stage = self._determine_next_stage(defn, state)
        if next_stage is not None:
            state.current_stage = next_stage
            if state.status == ProductionStatus.BLOCKED or state.status == ProductionStatus.FAILED:
                state.status = ProductionStatus.RUNNING
        else:
            self._check_and_mark_completion(defn, state)

        self.state_store.save(state)
        self._get_checkpoint_store(project_id).create_checkpoint(
            state, "production_resumed", stage=state.current_stage, message=f"Resumed at stage {state.current_stage}"
        )
        self._get_audit_log(project_id).record(
            "production_resumed", stage=state.current_stage, message=f"Resumed production at {state.current_stage}"
        )
        return state

    def status(self, project_id: str) -> dict[str, Any]:
        """Return a structured summary of the production state and lineage."""
        state = self.state_store.load(project_id)
        defn = self._get_pipeline(state.pipeline)
        chk_store = self._get_checkpoint_store(project_id)
        last_chk = chk_store.get_latest_checkpoint()
        stale = find_stale_artifacts(state, self.artifact_store)

        return {
            "project_id": state.project_id,
            "pipeline": state.pipeline,
            "pipeline_version": state.pipeline_version,
            "status": state.status.value,
            "current_stage": state.current_stage,
            "run_mode": state.run_mode.value,
            "target_duration": state.target_duration,
            "active_artifact_versions": dict(state.active_artifact_versions),
            "stale_artifacts": stale,
            "revision_count": dict(state.revision_count),
            "budget": {
                "budget_cap": state.budget.budget_cap,
                "actual_cost": state.budget.actual_cost,
                "remaining_budget": state.budget.remaining_budget,
                "is_over_budget": state.budget.is_over_budget,
            },
            "last_checkpoint": last_chk.model_dump() if last_chk else None,
            "created_at": state.created_at.isoformat(),
            "updated_at": state.updated_at.isoformat(),
        }

    def run_next_stage(self, project_id: str) -> StageResult:
        """Run the current runnable stage in the pipeline."""
        state = self.state_store.load(project_id)
        if state.status == ProductionStatus.ABORTED:
            return StageResult(
                status=StageResultStatus.BLOCKED,
                stage=state.current_stage or "",
                message=f"Production {project_id!r} is aborted.",
            )

        if state.status == ProductionStatus.COMPLETED:
            return StageResult(
                status=StageResultStatus.READY,
                stage="completed",
                message=f"Production {project_id!r} is already completed.",
            )

        defn = self._get_pipeline(state.pipeline)

        # Idempotency check: if current_stage is already produced & approved, advance
        current_stage = state.current_stage or defn.required_stages[0]
        stage_def = defn.stages.get(current_stage)

        if stage_def and stage_def.produces:
            prod_type = stage_def.produces[0]
            active_ver = state.get_active_version(prod_type)
            if active_ver is not None:
                try:
                    art = self.artifact_store.load(prod_type, project_id, version=active_ver)
                    if art.status == ArtifactStatus.APPROVED:
                        # Advance to next uncompleted stage
                        next_stage = self._determine_next_stage(defn, state)
                        if next_stage is None:
                            self._check_and_mark_completion(defn, state)
                            return StageResult(
                                status=StageResultStatus.READY,
                                stage="completed",
                                message="All stages completed",
                            )
                        current_stage = next_stage
                        state.current_stage = current_stage
                        self.state_store.save(state)
                except Exception:
                    pass

        # Transition to RUNNING
        state.status = ProductionStatus.RUNNING
        state.current_stage = current_stage
        self.state_store.save(state)

        # Checkpoint: stage_started
        self._get_checkpoint_store(project_id).create_checkpoint(
            state, "stage_started", stage=current_stage, message=f"Starting stage {current_stage}"
        )
        self._get_audit_log(project_id).record(
            "stage_started", stage=current_stage, message=f"Starting stage {current_stage}"
        )

        # Execute stage via StageRunner
        result = self.stage_runner.run(current_stage, defn, state)

        # Handle result
        if result.status == StageResultStatus.READY:
            effective_app = defn.effective_approval(current_stage, state.run_mode)
            if effective_app == ApprovalMode.AUTO:
                # Auto-approve
                if result.artifact_type and result.artifact_version:
                    self.artifact_store.approve(
                        result.artifact_type, project_id, result.artifact_version, actor="system_auto"
                    )
                    state.add_decision(
                        current_stage,
                        decision=f"Auto-approved {result.artifact_type} v{result.artifact_version}",
                        reason="Quality gates passed and pipeline approval policy is auto",
                        actor="system",
                    )
                # Advance stage
                next_stage = self._determine_next_stage(defn, state)
                state.current_stage = next_stage
                if next_stage is None:
                    self._check_and_mark_completion(defn, state)
                else:
                    state.status = ProductionStatus.RUNNING
            else:
                state.status = ProductionStatus.WAITING_APPROVAL

            self.state_store.save(state)
            self._get_checkpoint_store(project_id).create_checkpoint(
                state, "stage_completed", stage=current_stage, message=result.message
            )
            self._get_audit_log(project_id).record(
                "stage_completed", stage=current_stage, details={"result": result.model_dump()}, message=result.message
            )

        elif result.status == StageResultStatus.WAITING_APPROVAL:
            state.status = ProductionStatus.WAITING_APPROVAL
            self.state_store.save(state)
            self._get_checkpoint_store(project_id).create_checkpoint(
                state, "stage_waiting_approval", stage=current_stage, message=result.message
            )
            self._get_audit_log(project_id).record(
                "stage_waiting_approval", stage=current_stage, message=result.message
            )

        elif result.status == StageResultStatus.BLOCKED:
            state.status = ProductionStatus.BLOCKED
            self.state_store.save(state)
            self._get_checkpoint_store(project_id).create_checkpoint(
                state, "stage_blocked", stage=current_stage, message=result.message
            )
            self._get_audit_log(project_id).record(
                "stage_blocked", stage=current_stage, severity=Severity.WARNING, message=result.message
            )

        elif result.status == StageResultStatus.NOT_IMPLEMENTED:
            state.status = ProductionStatus.BLOCKED
            state.add_warning("STAGE_NOT_IMPLEMENTED", current_stage, result.message, Severity.WARNING)
            self.state_store.save(state)
            self._get_checkpoint_store(project_id).create_checkpoint(
                state, "stage_not_implemented", stage=current_stage, message=result.message
            )
            self._get_audit_log(project_id).record(
                "stage_not_implemented", stage=current_stage, severity=Severity.WARNING, message=result.message
            )

        elif result.status == StageResultStatus.FAILED:
            state.status = ProductionStatus.FAILED
            state.add_error("STAGE_FAILED", current_stage, result.message, Severity.ERROR, recoverable=True)
            self.state_store.save(state)
            self._get_checkpoint_store(project_id).create_checkpoint(
                state, "stage_failed", stage=current_stage, message=result.message
            )
            self._get_audit_log(project_id).record(
                "stage_failed", stage=current_stage, severity=Severity.ERROR, message=result.message
            )

        return result

    def run_stage(
        self,
        project_id: str,
        stage_name: str,
        notes: str = "",
        **kwargs: Any,
    ) -> StageResult:
        """Explicitly run a named stage in the pipeline."""
        state = self.state_store.load(project_id)
        if state.status == ProductionStatus.ABORTED:
            return StageResult(
                status=StageResultStatus.BLOCKED,
                stage=stage_name,
                message=f"Production {project_id!r} is aborted.",
            )

        defn = self._get_pipeline(state.pipeline)
        state.status = ProductionStatus.RUNNING
        state.current_stage = stage_name
        self.state_store.save(state)

        self._get_checkpoint_store(project_id).create_checkpoint(
            state, "stage_started", stage=stage_name, message=f"Starting stage {stage_name}"
        )
        self._get_audit_log(project_id).record(
            "stage_started", stage=stage_name, message=f"Starting stage {stage_name}"
        )

        result = self.stage_runner.run(stage_name, defn, state, notes=notes, **kwargs)

        if result.status == StageResultStatus.READY:
            effective_app = defn.effective_approval(stage_name, state.run_mode)
            if effective_app == ApprovalMode.AUTO:
                if result.artifact_type and result.artifact_version:
                    self.artifact_store.approve(
                        result.artifact_type, project_id, result.artifact_version, actor="system_auto"
                    )
                    state.add_decision(
                        stage_name,
                        decision=f"Auto-approved {result.artifact_type} v{result.artifact_version}",
                        reason="Quality gates passed and pipeline approval policy is auto",
                        actor="system",
                    )
                next_stage = self._determine_next_stage(defn, state)
                state.current_stage = next_stage
                if next_stage is None:
                    self._check_and_mark_completion(defn, state)
                else:
                    state.status = ProductionStatus.RUNNING
            else:
                state.status = ProductionStatus.WAITING_APPROVAL

            self.state_store.save(state)
            self._get_checkpoint_store(project_id).create_checkpoint(
                state, "stage_completed", stage=stage_name, message=result.message
            )
            self._get_audit_log(project_id).record(
                "stage_completed", stage=stage_name, details={"result": result.model_dump()}, message=result.message
            )

        elif result.status == StageResultStatus.WAITING_APPROVAL:
            state.status = ProductionStatus.WAITING_APPROVAL
            self.state_store.save(state)
            self._get_checkpoint_store(project_id).create_checkpoint(
                state, "stage_waiting_approval", stage=stage_name, message=result.message
            )
            self._get_audit_log(project_id).record(
                "stage_waiting_approval", stage=stage_name, message=result.message
            )

        elif result.status == StageResultStatus.BLOCKED:
            state.status = ProductionStatus.BLOCKED
            self.state_store.save(state)
            self._get_checkpoint_store(project_id).create_checkpoint(
                state, "stage_blocked", stage=stage_name, message=result.message
            )
            self._get_audit_log(project_id).record(
                "stage_blocked", stage=stage_name, severity=Severity.WARNING, message=result.message
            )

        elif result.status == StageResultStatus.NOT_IMPLEMENTED:
            state.status = ProductionStatus.BLOCKED
            state.add_warning("STAGE_NOT_IMPLEMENTED", stage_name, result.message, Severity.WARNING)
            self.state_store.save(state)
            self._get_checkpoint_store(project_id).create_checkpoint(
                state, "stage_not_implemented", stage=stage_name, message=result.message
            )
            self._get_audit_log(project_id).record(
                "stage_not_implemented", stage=stage_name, severity=Severity.WARNING, message=result.message
            )

        elif result.status == StageResultStatus.FAILED:
            state.status = ProductionStatus.FAILED
            state.add_error("STAGE_FAILED", stage_name, result.message, Severity.ERROR, recoverable=True)
            self.state_store.save(state)
            self._get_checkpoint_store(project_id).create_checkpoint(
                state, "stage_failed", stage=stage_name, message=result.message
            )
            self._get_audit_log(project_id).record(
                "stage_failed", stage=stage_name, severity=Severity.ERROR, message=result.message
            )

        return result


    def run_until_blocked(self, project_id: str, max_stages: int = 20) -> list[StageResult]:
        """Execute stages sequentially until production blocks, requires approval, or completes."""
        results: list[StageResult] = []
        for _ in range(max_stages):
            res = self.run_next_stage(project_id)
            results.append(res)
            if res.status in (
                StageResultStatus.BLOCKED,
                StageResultStatus.WAITING_APPROVAL,
                StageResultStatus.FAILED,
                StageResultStatus.NOT_IMPLEMENTED,
            ):
                break
            state = self.state_store.load(project_id)
            if state.status == ProductionStatus.COMPLETED:
                break
        return results

    def retry_stage(self, project_id: str, stage_name: str) -> StageResult:
        """Retry a failed stage with the same inputs, incrementing revision count."""
        state = self.state_store.load(project_id)
        defn = self._get_pipeline(state.pipeline)

        state.increment_revision(stage_name)
        state.status = ProductionStatus.RUNNING
        state.current_stage = stage_name
        self.state_store.save(state)

        self._get_checkpoint_store(project_id).create_checkpoint(
            state, "stage_retried", stage=stage_name, message=f"Retrying stage {stage_name}"
        )
        self._get_audit_log(project_id).record(
            "stage_retried", stage=stage_name, message=f"Retry requested for {stage_name}"
        )
        return self.run_next_stage(project_id)

    def revise_stage(self, project_id: str, stage_name: str, notes: str) -> StageResult:
        """Revise a stage with feedback notes, incrementing revision and invalidating downstream."""
        state = self.state_store.load(project_id)
        defn = self._get_pipeline(state.pipeline)

        state.increment_revision(stage_name)
        state.status = ProductionStatus.RUNNING
        state.current_stage = stage_name

        # Invalidate downstream artifacts whose inputs will change
        stage_def = defn.stages.get(stage_name)
        if stage_def and stage_def.produces:
            invalidated = invalidate_downstream(stage_def.produces[0], defn, state, self.artifact_store)
            if invalidated:
                state.add_warning(
                    "DOWNSTREAM_INVALIDATED", stage_name,
                    f"Downstream artifacts invalidated due to revision of {stage_name}: {invalidated}",
                    Severity.INFO
                )

        self.state_store.save(state)
        self._get_checkpoint_store(project_id).create_checkpoint(
            state, "revision_requested", stage=stage_name, message=f"Revision notes: {notes}"
        )
        self._get_audit_log(project_id).record(
            "revision_requested", stage=stage_name, details={"notes": notes}, message=f"Revision of {stage_name}"
        )
        return self.stage_runner.run(stage_name, defn, state, notes=notes)

    def approve(self, project_id: str, stage_name: str, actor: str = "human") -> ProductionState:
        """Explicitly approve a stage artifact (e.g. at a human checkpoint)."""
        state = self.state_store.load(project_id)
        defn = self._get_pipeline(state.pipeline)
        stage_def = defn.stages.get(stage_name)
        if not stage_def or not stage_def.produces:
            raise ControllerError(f"Stage {stage_name!r} produces no artifacts to approve")

        prod_type = stage_def.produces[0]
        active_ver = state.get_active_version(prod_type)
        if active_ver is None:
            raise ControllerError(f"No active artifact version exists for stage {stage_name!r}")

        self.artifact_store.approve(prod_type, project_id, active_ver, actor=actor)
        state.add_decision(
            stage_name,
            decision=f"Approved {prod_type} v{active_ver}",
            reason="Human/reviewer approval granted",
            actor=actor,
        )

        # Advance current stage
        next_stage = self._determine_next_stage(defn, state)
        state.current_stage = next_stage
        if next_stage is None:
            self._check_and_mark_completion(defn, state)
        else:
            state.status = ProductionStatus.RUNNING

        self.state_store.save(state)
        self._get_checkpoint_store(project_id).create_checkpoint(
            state, "artifact_approved", stage=stage_name, message=f"Approved {prod_type} v{active_ver}"
        )
        self._get_audit_log(project_id).record(
            "artifact_approved", stage=stage_name, actor=actor, message=f"Approved {prod_type} v{active_ver}"
        )
        return state

    def reject(
        self,
        project_id: str,
        stage_name: str,
        reason: str = "",
        actor: str = "human",
    ) -> ProductionState:
        """Reject a stage output, invalidate downstream artifacts, and set stage for revision."""
        state = self.state_store.load(project_id)
        defn = self._get_pipeline(state.pipeline)
        stage_def = defn.stages.get(stage_name)
        if not stage_def or not stage_def.produces:
            raise ControllerError(f"Stage {stage_name!r} produces no artifacts to reject")

        prod_type = stage_def.produces[0]
        active_ver = state.get_active_version(prod_type)
        if active_ver is None:
            raise ControllerError(f"No active artifact exists to reject for stage {stage_name!r}")

        self.artifact_store.reject(prod_type, project_id, active_ver, reason=reason)
        state.add_decision(
            stage_name,
            decision=f"Rejected {prod_type} v{active_ver}",
            reason=reason or "Rejected by user/reviewer",
            actor=actor,
        )

        # Increment revision counter
        state.increment_revision(stage_name)

        # Invalidate downstream
        invalidate_downstream(prod_type, defn, state, self.artifact_store)

        state.status = ProductionStatus.BLOCKED
        state.current_stage = stage_name
        self.state_store.save(state)

        self._get_checkpoint_store(project_id).create_checkpoint(
            state, "artifact_rejected", stage=stage_name, message=f"Rejected {prod_type} v{active_ver}: {reason}"
        )
        self._get_audit_log(project_id).record(
            "artifact_rejected", stage=stage_name, actor=actor, details={"reason": reason}, message=f"Rejected {prod_type} v{active_ver}"
        )
        return state

    def abort(self, project_id: str, reason: str = "") -> ProductionState:
        """Cancel a production, halting any new stage executions while preserving history."""
        state = self.state_store.load(project_id)
        state.status = ProductionStatus.ABORTED
        state.add_decision(
            state.current_stage or "pipeline",
            decision="Aborted production",
            reason=reason or "User cancelled",
            actor="human",
        )
        self.state_store.save(state)

        self._get_checkpoint_store(project_id).create_checkpoint(
            state, "production_aborted", message=f"Production aborted: {reason}"
        )
        self._get_audit_log(project_id).record(
            "production_aborted", details={"reason": reason}, message=f"Production {project_id} aborted"
        )
        return state

    def rerender(self, project_id: str) -> dict[str, Any]:
        """Validate rerender feasibility without invoking any actual renderer."""
        state = self.state_store.load(project_id)
        if state.status == ProductionStatus.ABORTED:
            return {
                "status": "blocked",
                "reason": f"Production {project_id} is aborted",
            }

        defn = self._get_pipeline(state.pipeline)

        # Check if edit_decisions exists and is approved
        edit_ver = state.get_active_version("edit_decisions")
        if edit_ver is None:
            return {
                "status": "blocked",
                "reason": "No active 'edit_decisions' artifact exists. Run pipeline through edit stage first.",
            }

        try:
            art = self.artifact_store.load("edit_decisions", project_id, version=edit_ver)
            if art.status not in (ArtifactStatus.APPROVED, ArtifactStatus.READY):
                return {
                    "status": "blocked",
                    "reason": f"'edit_decisions' v{edit_ver} has status '{art.status.value}', expected approved/ready",
                }
        except Exception as exc:
            return {"status": "blocked", "reason": f"Error loading edit_decisions: {exc}"}

        # Check for staleness
        stale_map = find_stale_artifacts(state, self.artifact_store)
        if "edit_decisions" in stale_map:
            return {
                "status": "blocked",
                "reason": f"'edit_decisions' is stale: {stale_map['edit_decisions']}",
            }

        return {
            "status": "ready_to_render",
            "production_id": project_id,
            "runtime": defn.render_runtime_policy.primary,
            "edit_decisions_version": edit_ver,
            "message": "Approved edit decisions verified. Ready for composition runtime.",
        }
