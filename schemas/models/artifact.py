"""Pydantic V2 models for artifact envelopes, versioning, provenance, and state."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

from .common import ArtifactStatus, ProducerKind


class ProducerInfo(BaseModel):
    """Who or what produced this artifact — full provenance record."""
    kind: ProducerKind
    provider: str | None = None          # e.g. "gemini", "openai", "openrouter"
    model: str | None = None             # e.g. "gemini-2.0-flash"
    tool: str | None = None              # e.g. "edge-tts", "ffmpeg"
    prompt_hash: str | None = None       # sha256 of the prompt used
    source_artifacts: list["ArtifactReference"] = Field(default_factory=list)
    estimated_cost: float | None = None  # USD
    actual_cost: float | None = None     # USD, filled after billing

    model_config = {"extra": "forbid"}


class ArtifactReference(BaseModel):
    """Immutable pointer to a specific artifact version — used for dependency tracking."""
    artifact_type: str
    version: int
    content_hash: str  # sha256:... of the referenced artifact's data field

    model_config = {"extra": "forbid"}

    @field_validator("content_hash")
    @classmethod
    def validate_hash_format(cls, v: str) -> str:
        if not v.startswith("sha256:"):
            raise ValueError(f"content_hash must start with 'sha256:', got: {v!r}")
        hex_part = v[7:]
        if len(hex_part) != 64:
            raise ValueError(f"SHA-256 hex digest must be 64 chars, got {len(hex_part)}")
        return v


class ArtifactEnvelope(BaseModel):
    """The common wrapper around every persisted artifact in the production system.

    Every artifact — regardless of type — is stored inside this envelope.
    The 'data' field contains the artifact-type-specific payload.
    """
    artifact_type: str
    schema_version: str = "2.0"
    artifact_version: int = Field(ge=1)
    production_id: str
    stage: str
    status: ArtifactStatus
    created_at: datetime
    updated_at: datetime
    producer: ProducerInfo
    content_hash: str           # sha256:... of canonical JSON of 'data'
    data: dict[str, Any]

    # Optional fields
    parent_artifacts: list[ArtifactReference] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = {"extra": "forbid"}

    @field_validator("content_hash")
    @classmethod
    def validate_hash_format(cls, v: str) -> str:
        if not v.startswith("sha256:"):
            raise ValueError(f"content_hash must start with 'sha256:', got: {v!r}")
        hex_part = v[7:]
        if len(hex_part) != 64:
            raise ValueError(f"SHA-256 hex digest must be 64 chars, got {len(hex_part)}")
        return v

    @field_validator("schema_version")
    @classmethod
    def validate_schema_version(cls, v: str) -> str:
        if not v:
            raise ValueError("schema_version must not be empty")
        return v

    @field_validator("artifact_type")
    @classmethod
    def validate_artifact_type(cls, v: str) -> str:
        if not v or not v.replace("_", "").isalnum():
            raise ValueError(f"artifact_type must be alphanumeric with underscores, got: {v!r}")
        return v

    @field_validator("production_id")
    @classmethod
    def validate_production_id(cls, v: str) -> str:
        if not v or len(v) < 3:
            raise ValueError(f"production_id must be at least 3 chars, got: {v!r}")
        return v

    @model_validator(mode="after")
    def validate_timestamps(self) -> "ArtifactEnvelope":
        if self.updated_at < self.created_at:
            raise ValueError("updated_at must be >= created_at")
        return self


class ArtifactState(BaseModel):
    """Summary of an artifact's current versioning and approval state.

    Stored in ProductionState.artifacts for quick access without loading full envelopes.
    """
    artifact_type: str
    latest_version: int = Field(ge=1)
    active_version: int = Field(ge=1)
    status: ArtifactStatus
    content_hash: str
    stage: str
    updated_at: datetime

    model_config = {"extra": "forbid"}

    @model_validator(mode="after")
    def validate_active_le_latest(self) -> "ArtifactState":
        if self.active_version > self.latest_version:
            raise ValueError(
                f"active_version ({self.active_version}) cannot exceed "
                f"latest_version ({self.latest_version})"
            )
        return self
