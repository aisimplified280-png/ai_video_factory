"""Data models and serialization structures for the Phase 5 Asset Manifest."""
from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field


class AssetItem(BaseModel):
    """Canonical model for a single planned or generated asset."""
    asset_id: str
    scene_id: str
    purpose: str = Field(min_length=5)
    visual_role: str = "primary"  # primary, secondary, background, overlay, transitional
    type: Literal[
        "image",
        "video",
        "diagram",
        "chart",
        "code",
        "screenshot",
        "screen_recording",
        "logo",
        "icon",
        "music",
        "voice",
        "sfx",
        "background",
        "animation",
        "svg",
        "texture",
        "native_composition",
    ] = "image"
    source: Literal[
        "generated",
        "stock",
        "native",
        "local",
        "remote",
        "web",
        "local_library",
        "hybrid",
    ] = "generated"
    provider: str | None = None
    model: str | None = None
    prompt: str | None = None
    negative_prompt: str | None = None
    reference_assets: list[str] = Field(default_factory=list)
    expected_duration: float | None = None
    quality_requirements: dict[str, Any] = Field(default_factory=dict)
    fallback_chain: list[str] = Field(default_factory=list)
    file_path: str | None = None
    status: Literal["pending", "generating", "ready", "failed", "needs_review"] = "pending"
    cost_usd: float | None = 0.0

    # Semantic inheritance & strategy fields
    subject: str = ""
    subject_action: str = ""
    environment: str = ""
    composition_requirements: str = ""
    camera_requirements: str = ""
    motion_requirements: str = ""
    style_requirements: str = ""
    continuity_requirements: str = ""
    source_strategy: str = "generated"
    provider_strategy: str = ""
    fallback_used: str | None = None
    diagram_spec: dict[str, Any] | None = None

    # QA and score metrics
    technical_score: float | None = None
    semantic_fit: float | None = None
    continuity_fit: float | None = None
    quality_score: float | None = None
    qa_finding: str | None = None

    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = {"extra": "ignore"}

    def to_schema_dict(self) -> dict[str, Any]:
        """Convert to dict conforming strictly to asset_manifest.schema.json."""
        d = self.model_dump(exclude_none=False)
        # Ensure fallback_chain is list
        if d.get("fallback_chain") is None:
            d["fallback_chain"] = []
        if d.get("reference_assets") is None:
            d["reference_assets"] = []
        return d


class AssetManifestPayload(BaseModel):
    """Payload stored in ArtifactEnvelope.data for asset_manifest."""
    assets: list[AssetItem] = Field(default_factory=list)
    total_estimated_cost: float = Field(default=0.0, ge=0.0)
    actual_cost: float = Field(default=0.0, ge=0.0)
    medium_distribution: dict[str, int] = Field(default_factory=dict)
    source_distribution: dict[str, int] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = {"extra": "ignore"}

    def to_schema_dict(self) -> dict[str, Any]:
        return {
            "assets": [a.to_schema_dict() for a in self.assets],
            "total_estimated_cost": round(self.total_estimated_cost, 4),
            "actual_cost": round(self.actual_cost, 4),
            "medium_distribution": self.medium_distribution,
            "source_distribution": self.source_distribution,
            "metadata": self.metadata,
        }


class AssetReviewReport(BaseModel):
    """Comprehensive asset review report for technical and semantic QA."""
    production_id: str
    overall_status: Literal["pass", "warning", "reject", "needs_review"] = "pass"
    average_technical_score: float = 0.0
    average_semantic_fit: float = 0.0
    average_continuity_fit: float = 0.0
    reviews: list[dict[str, Any]] = Field(default_factory=list)

    model_config = {"extra": "ignore"}


class AssetGenerationReport(BaseModel):
    """Execution and audit record for every attempted asset generation."""
    production_id: str
    total_cost_usd: float = 0.0
    total_time_seconds: float = 0.0
    generation_attempts: list[dict[str, Any]] = Field(default_factory=list)

    model_config = {"extra": "ignore"}
