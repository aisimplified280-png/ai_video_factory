"""Pydantic models for Phase 12 YouTube Packaging Intelligence."""
from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, Field
from ..phase11.models import ScriptArtifact


class TitleCandidate(BaseModel):
    title: str
    angle: str  # curiosity_gap | shock_revelation | authority | extreme_shift | metric_proof
    title_score: float = 8.5      # 0.0 - 10.0 heuristic rating
    curiosity_score: float = 8.8  # 0.0 - 10.0 curiosity rating

    class Config:
        extra = "allow"


class TopicPackage(BaseModel):
    topic: str
    selected_title: str
    title_candidates: list[TitleCandidate] = Field(default_factory=list)
    description: str = ""
    hashtags: list[str] = Field(default_factory=list)
    thumbnail_text: str = ""
    thumbnail_prompt: str = ""
    title_score: float = 9.2
    curiosity_score: float = 9.0
    thumbnail_score: float = 8.8
    overall_package_score: float = 9.0
    script_shorts: Optional[ScriptArtifact] = None
    script_longform: Optional[ScriptArtifact] = None

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump()

    class Config:
        extra = "allow"
