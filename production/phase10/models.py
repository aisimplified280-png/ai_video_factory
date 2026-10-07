"""Pydantic models for the Phase 10 research pack artifact."""
from __future__ import annotations

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class ClaimStatus(str, Enum):
    CONFIRMED = "CONFIRMED"
    LIKELY = "LIKELY"
    SINGLE_SOURCE = "SINGLE_SOURCE"
    CONFLICTING = "CONFLICTING"
    UNVERIFIED = "UNVERIFIED"
    OUTDATED = "OUTDATED"


class ResearchMode(str, Enum):
    LIVE = "live"
    UNAVAILABLE = "unavailable"


class SourceRecord(BaseModel):
    source_id: str
    title: str
    publisher: str
    url: str  # stored as string since we need to handle partial URLs
    published_at: Optional[str] = None   # ISO-8601 or None
    retrieved_at: str
    source_type: str  # official | news | paper | social | other
    query: str = ""
    retrieval_provider: str = ""
    tier: int = 3  # 1=official, 2=high-repute news, 3=secondary, 4=social
    snippet: str = ""

    class Config:
        extra = "allow"


class ClaimRecord(BaseModel):
    claim_id: str
    claim: str
    status: ClaimStatus
    confidence: float  # 0.0 - 1.0
    source_ids: list[str]
    primary_source_id: Optional[str] = None
    notes: str = ""

    class Config:
        extra = "allow"


class VisualFactPack(BaseModel):
    visual_keywords: list[str] = Field(default_factory=list)
    entities: list[str] = Field(default_factory=list)
    locations: list[str] = Field(default_factory=list)
    objects: list[str] = Field(default_factory=list)
    actions: list[str] = Field(default_factory=list)
    visual_prompt_seed: str = ""
    anti_cliche_notes: str = ""

    class Config:
        extra = "allow"


class StoryScoring(BaseModel):
    relevance: float = 0.0         # 0.0 - 1.0 (semantic topic match)
    virality: float = 0.0          # 0.0 - 1.0
    subscriber_potential: float = 0.0 # 0.0 - 1.0
    shock_factor: float = 0.0      # 0.0 - 1.0
    visual_potential: float = 0.0  # 0.0 - 1.0
    trust_score: float = 0.0       # 0.0 - 1.0
    overall_score: float = 0.0     # composite weighted score

    class Config:
        extra = "allow"


class StoryRecord(BaseModel):
    story_id: str
    headline: str
    summary: str = ""
    source_ids: list[str] = Field(default_factory=list)
    primary_source_id: Optional[str] = None
    trust_score: float = 0.5
    visual_facts: VisualFactPack = Field(default_factory=VisualFactPack)
    scoring: StoryScoring = Field(default_factory=StoryScoring)
    rank: int = 0

    class Config:
        extra = "allow"


class ResearchPack(BaseModel):
    topic: str
    researched_at: str
    research_mode: ResearchMode
    provider: Optional[str] = None
    queries_issued: list[str] = Field(default_factory=list)
    claims: list[ClaimRecord] = Field(default_factory=list)
    sources: list[SourceRecord] = Field(default_factory=list)
    visual_facts: VisualFactPack = Field(default_factory=VisualFactPack)
    stories: list[StoryRecord] = Field(default_factory=list)
    top_stories: list[StoryRecord] = Field(default_factory=list)
    status: str = "ok"   # "ok" | "LIVE_RESEARCH_UNAVAILABLE"

    class Config:
        extra = "allow"

    def to_dict(self) -> dict:
        return self.model_dump()
