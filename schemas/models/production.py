"""Pydantic V2 models for ProductionState and associated structures."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field, field_validator, computed_field

from .common import ProductionStatus, Severity, RunMode
from .artifact import ArtifactState


# ---------------------------------------------------------------------------
# Budget
# ---------------------------------------------------------------------------

class BudgetState(BaseModel):
    """Tracks costs and enforces budget caps for a production."""
    budget_cap: float = Field(default=10.0, ge=0)
    estimated_cost: float = Field(default=0.0, ge=0)
    reserved_cost: float = Field(default=0.0, ge=0)
    actual_cost: float = Field(default=0.0, ge=0)

    model_config = {"extra": "ignore"}

    @property
    def remaining_budget(self) -> float:
        return max(0.0, self.budget_cap - self.actual_cost)

    @property
    def is_over_budget(self) -> bool:
        return self.actual_cost > self.budget_cap

    def can_spend(self, amount: float) -> bool:
        """Return True if spending `amount` would stay within budget cap."""
        return (self.actual_cost + amount) <= self.budget_cap


# ---------------------------------------------------------------------------
# Decision / Warning / Error
# ---------------------------------------------------------------------------

class Decision(BaseModel):
    """A recorded decision made during a production (human or system)."""
    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    stage: str
    decision: str
    reason: str
    created_at: datetime
    actor: str  # "system", "human", or a user identifier

    model_config = {"extra": "forbid"}


class Warning(BaseModel):
    """A non-blocking issue that should be noted but does not halt the production."""
    code: str                  # Machine-readable identifier, e.g. "LOW_SOURCE_COUNT"
    stage: str
    message: str
    severity: Severity = Severity.WARNING

    model_config = {"extra": "forbid"}


class ProductionError(BaseModel):
    """A blocking or critical issue that may halt or abort the production."""
    code: str
    stage: str
    message: str
    severity: Severity = Severity.ERROR
    recoverable: bool = True   # If True, a revision of the stage may fix it

    model_config = {"extra": "forbid"}


# ---------------------------------------------------------------------------
# ProductionState
# ---------------------------------------------------------------------------

class ProductionState(BaseModel):
    """The complete, persistent state of one production.

    This is the single authoritative record of where a production is,
    what artifacts have been produced, and what decisions have been made.

    Never store renderer state or stage logic here — only lifecycle facts.
    """
    project_id: str
    pipeline: str                              # e.g. "youtube-short"
    pipeline_version: str                      # e.g. "2.0"
    run_mode: RunMode = RunMode.AUTO

    status: ProductionStatus = ProductionStatus.CREATED
    current_stage: str | None = None

    # Platform / creative parameters
    target_duration: float = Field(ge=0)
    aspect_ratio: str                          # e.g. "9:16"
    platform: str                              # e.g. "youtube_shorts"
    style: str = "auto"

    # Budget
    budget: BudgetState = Field(default_factory=BudgetState)

    # Artifacts: keyed by artifact_type
    artifacts: dict[str, ArtifactState] = Field(default_factory=dict)

    # Which version of each artifact is currently active (approved or latest ready)
    # e.g. {"research_brief": 2, "script": 3}
    active_artifact_versions: dict[str, int] = Field(default_factory=dict)

    # Audit trail
    decisions: list[Decision] = Field(default_factory=list)
    warnings: list[Warning] = Field(default_factory=list)
    errors: list[ProductionError] = Field(default_factory=list)

    # Per-stage revision counters: {"scene_plan": 2}
    revision_count: dict[str, int] = Field(default_factory=dict)

    # Timestamps
    created_at: datetime
    updated_at: datetime

    # Arbitrary extra metadata (e.g. topic, user notes)
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = {"extra": "forbid"}

    @field_validator("project_id")
    @classmethod
    def validate_project_id(cls, v: str) -> str:
        if not v or len(v) < 3:
            raise ValueError(f"project_id must be at least 3 chars, got: {v!r}")
        return v

    @field_validator("aspect_ratio")
    @classmethod
    def validate_aspect_ratio(cls, v: str) -> str:
        valid = {"9:16", "16:9", "1:1", "4:3", "3:4"}
        if v not in valid:
            raise ValueError(f"aspect_ratio must be one of {valid}, got: {v!r}")
        return v

    def get_active_version(self, artifact_type: str) -> int | None:
        """Return the currently active version number for an artifact type, or None."""
        return self.active_artifact_versions.get(artifact_type)

    def set_active_version(self, artifact_type: str, version: int) -> None:
        """Mark a version as the active (approved/current) version."""
        self.active_artifact_versions[artifact_type] = version

    def increment_revision(self, stage: str) -> int:
        """Increment and return the revision count for a stage."""
        self.revision_count[stage] = self.revision_count.get(stage, 0) + 1
        return self.revision_count[stage]

    def get_revision_count(self, stage: str) -> int:
        """Return current revision count for a stage (0 if not yet revised)."""
        return self.revision_count.get(stage, 0)

    def add_decision(self, stage: str, decision: str, reason: str, actor: str = "system") -> None:
        """Record a decision to the audit trail."""
        from datetime import datetime, timezone
        self.decisions.append(Decision(
            stage=stage, decision=decision, reason=reason,
            actor=actor, created_at=datetime.now(timezone.utc)
        ))

    def add_warning(self, code: str, stage: str, message: str,
                    severity: Severity = Severity.WARNING) -> None:
        self.warnings.append(Warning(code=code, stage=stage, message=message, severity=severity))

    def add_error(self, code: str, stage: str, message: str,
                  severity: Severity = Severity.ERROR, recoverable: bool = True) -> None:
        self.errors.append(ProductionError(
            code=code, stage=stage, message=message,
            severity=severity, recoverable=recoverable
        ))

    def to_json(self, indent: int = 2) -> str:
        """Serialize to JSON string."""
        return self.model_dump_json(indent=indent)

    @classmethod
    def from_json(cls, json_str: str) -> "ProductionState":
        """Deserialize from JSON string."""
        return cls.model_validate_json(json_str)
