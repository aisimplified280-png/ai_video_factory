"""Pydantic models for Phase 11 Script Intelligence."""
from __future__ import annotations

from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field


class ScriptFormat(str, Enum):
    SHORTS = "shorts"
    LONG_FORM = "long_form"


class ScriptSection(BaseModel):
    section_id: str
    scene_id: str
    role: str   # hook | lead_story | escalation | tool_discovery | cta
    spoken_text: str
    estimated_duration_seconds: float
    word_count: int
    emphasis_words: list[str] = Field(default_factory=list)
    visual_intent: str = "reveal"
    primary_subject: str = ""
    retention_trigger: str = "fast_pacing"

    class Config:
        extra = "allow"


class ScriptScore(BaseModel):
    retention_score: float = 0.85             # 0.0 - 1.0
    hook_strength_score: float = 0.90         # 0.0 - 1.0
    subscriber_conversion_score: float = 0.88 # 0.0 - 1.0
    word_pacing_wpm: float = 160.0            # Words Per Minute

    class Config:
        extra = "allow"


class ScriptArtifact(BaseModel):
    topic: str
    format: ScriptFormat
    hook_story_id: str
    sections: list[ScriptSection] = Field(default_factory=list)
    total_duration_seconds: float = 0.0
    total_word_count: int = 0
    scoring: ScriptScore = Field(default_factory=ScriptScore)
    grounded_claims: list[str] = Field(default_factory=list)
    channel_name: str = "AI Simplified Lab"

    def to_canonical_schema(self, production_id: str) -> dict[str, Any]:
        """Produce canonical data payload matching schemas/artifacts/script.schema.json."""
        role_map = {
            "hook": "hook",
            "lead_story": "reveal",
            "escalation": "mechanism",
            "implication": "implication",
            "cta": "cta",
        }
        return {
            "schema_version": "1.0",
            "production_id": production_id,
            "target_duration_seconds": round(self.total_duration_seconds, 1),
            "word_count": self.total_word_count,
            "sections": [
                {
                    "id": s.section_id,
                    "section_id": s.section_id,
                    "scene_id": s.scene_id,
                    "spoken_text": s.spoken_text,
                    "narrative_role": role_map.get(s.role, "context"),
                    "primary_subject": s.primary_subject or self.topic,
                    "primary_intent": s.visual_intent,
                    "emphasis_words": s.emphasis_words,
                    "estimated_duration": s.estimated_duration_seconds,
                }
                for s in self.sections
            ],
            "script_scoring": self.scoring.model_dump(),
        }

    class Config:
        extra = "allow"
