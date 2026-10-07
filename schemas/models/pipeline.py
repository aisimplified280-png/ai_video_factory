"""Pydantic V2 models for pipeline definitions, stage contracts, and policies."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator

from .common import ApprovalMode, QualityGateType, RunMode


# ---------------------------------------------------------------------------
# Quality Gates
# ---------------------------------------------------------------------------

class QualityGate(BaseModel):
    """A machine-evaluable pass/fail criterion for a stage output."""
    name: str                           # Human-readable label, e.g. "min_source_count"
    type: QualityGateType
    field: str                          # Dot-path into artifact data, e.g. "sources"
    threshold: float | None = None      # For MIN/MAX gates
    pattern: str | None = None          # For REGEX gates
    required: bool = True               # False = warning-only, not blocking
    message: str = ""                   # Human-readable failure message

    model_config = {"extra": "forbid"}

    @field_validator("threshold")
    @classmethod
    def validate_threshold(cls, v: float | None) -> float | None:
        if v is not None and v < 0:
            raise ValueError(f"threshold must be >= 0, got {v}")
        return v


# ---------------------------------------------------------------------------
# Policies
# ---------------------------------------------------------------------------

class ApprovalPolicy(BaseModel):
    """Controls how a stage artifact is approved."""
    mode: ApprovalMode = ApprovalMode.AUTO

    model_config = {"extra": "forbid"}


class BudgetPolicy(BaseModel):
    """Per-pipeline spending limits."""
    budget_cap: float = Field(default=10.0, ge=0)
    max_image_gen_calls: int = Field(default=20, ge=0)
    max_video_gen_calls: int = Field(default=5, ge=0)
    max_tts_chars: int = Field(default=5000, ge=0)
    max_llm_tokens: int = Field(default=100_000, ge=0)

    model_config = {"extra": "forbid"}


class RenderRuntimePolicy(BaseModel):
    """Controls composition runtime selection and fallback behaviour.

    strict=True means: if the primary runtime is unavailable, return a hard
    blocker — do NOT silently substitute another runtime.
    """
    primary: str                        # "remotion", "hyperframes", "ffmpeg_pil"
    fallback: str | None = None         # Only used when strict=False
    strict: bool = True

    model_config = {"extra": "forbid"}

    @field_validator("primary")
    @classmethod
    def validate_primary(cls, v: str) -> str:
        valid = {"remotion", "hyperframes", "ffmpeg_pil"}
        if v not in valid:
            raise ValueError(f"render runtime must be one of {valid}, got: {v!r}")
        return v

    @field_validator("fallback")
    @classmethod
    def validate_fallback(cls, v: str | None) -> str | None:
        if v is not None:
            valid = {"remotion", "hyperframes", "ffmpeg_pil"}
            if v not in valid:
                raise ValueError(f"fallback runtime must be one of {valid}, got: {v!r}")
        return v


# ---------------------------------------------------------------------------
# Stage Definition
# ---------------------------------------------------------------------------

class StageDefinition(BaseModel):
    """Machine-readable contract for a single pipeline stage.

    Phase 2 controller uses this to determine:
    - whether a stage is runnable (all consumed artifacts exist)
    - what it will produce
    - how many revisions are allowed
    - whether human approval is needed
    """
    name: str
    required: bool = True
    produces: list[str]                 # artifact_types this stage outputs
    consumes: list[str]                 # artifact_types this stage requires as input
    approval: ApprovalPolicy = Field(default_factory=ApprovalPolicy)
    max_revisions: int = Field(default=3, ge=1, le=10)
    quality_gates: list[QualityGate] = Field(default_factory=list)
    description: str = ""               # Human-readable purpose of this stage

    model_config = {"extra": "forbid"}


# ---------------------------------------------------------------------------
# Pipeline Definition
# ---------------------------------------------------------------------------

class PipelineDefinition(BaseModel):
    """Complete machine-validated definition of a production pipeline.

    Loaded from YAML in pipeline_defs/. Every stage's dependencies are
    validated at load time via PipelineValidator before any production begins.
    """
    name: str
    version: str
    description: str
    target_duration: float = Field(ge=5)
    platform: str
    run_mode_default: RunMode = RunMode.AUTO

    # Stage ordering (list of stage names in execution order)
    required_stages: list[str]
    optional_stages: list[str] = Field(default_factory=list)

    # Artifacts that must be present for the production to be considered complete
    required_artifacts: list[str]

    # Full stage definitions (keyed by stage name)
    stages: dict[str, StageDefinition]

    # Pipeline-level quality gates (applied after final QA)
    quality_gates: list[QualityGate] = Field(default_factory=list)

    # Per-stage approval policies (overrides stage-level default)
    approval_policy: dict[str, ApprovalPolicy] = Field(default_factory=dict)

    # Policies
    budget_policy: BudgetPolicy = Field(default_factory=BudgetPolicy)
    render_runtime_policy: RenderRuntimePolicy = Field(
        default_factory=lambda: RenderRuntimePolicy(primary="remotion")
    )

    model_config = {"extra": "forbid"}

    @field_validator("required_stages")
    @classmethod
    def validate_nonempty_stages(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("required_stages must not be empty")
        return v

    def all_stage_names(self) -> list[str]:
        """Return all stages (required + optional) in order."""
        seen: set[str] = set()
        result: list[str] = []
        for name in self.required_stages + self.optional_stages:
            if name not in seen:
                seen.add(name)
                result.append(name)
        return result

    def get_stage(self, name: str) -> StageDefinition | None:
        return self.stages.get(name)

    def effective_approval(self, stage_name: str, run_mode: RunMode = RunMode.AUTO) -> ApprovalMode:
        """Return the effective approval mode for a stage given the run mode.

        In AUTO mode: always auto-approve unless stage has ALWAYS_AUTO override not needed.
        In GUIDED mode: human stages require human approval.
        In MANUAL mode: all stages can require human approval.
        """
        # Check pipeline-level override first
        if stage_name in self.approval_policy:
            policy = self.approval_policy[stage_name]
        elif stage_name in self.stages:
            policy = self.stages[stage_name].approval
        else:
            policy = ApprovalPolicy()

        if run_mode == RunMode.AUTO:
            return ApprovalMode.AUTO
        elif run_mode == RunMode.GUIDED:
            return policy.mode
        else:  # MANUAL
            return ApprovalMode.HUMAN
