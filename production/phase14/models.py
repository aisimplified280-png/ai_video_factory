"""Pydantic models for Phase 14 Factory Learning System."""
from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, Field


class VideoMetrics(BaseModel):
    """Empirical YouTube analytics metrics for published videos."""
    views: int = 0
    ctr_percent: float = 0.0               # e.g. 9.4 (%)
    avg_watch_percentage: float = 0.0      # e.g. 82.5 (%)
    subscribers_gained: int = 0
    retention_dropoff_3s: float = 0.0      # % retained at 3 seconds

    class Config:
        extra = "allow"


class VideoRecord(BaseModel):
    """Complete historical record of a produced and published video."""
    production_id: str
    topic: str
    selected_title: str
    title_angle: str = "curiosity_gap"
    hook_text: str = ""
    hook_style: str = "fast_assertion"
    visual_style: str = "documentary_industrial"
    thumbnail_text: str = ""
    metrics: VideoMetrics = Field(default_factory=VideoMetrics)
    composite_performance_score: float = 0.0  # 0.0 - 100.0
    recorded_at: str = ""

    class Config:
        extra = "allow"


class LearningInsights(BaseModel):
    """Aggregated insights synthesized across historical video performance."""
    total_videos_analyzed: int = 0
    top_title_angles: list[dict[str, Any]] = Field(default_factory=list)
    top_hook_patterns: list[dict[str, Any]] = Field(default_factory=list)
    top_visual_styles: list[dict[str, Any]] = Field(default_factory=list)
    winning_keywords: list[str] = Field(default_factory=list)
    underperforming_patterns: list[str] = Field(default_factory=list)
    recommended_title_angles: list[str] = Field(default_factory=list)
    recommended_visual_direction: str = "cinematic documentary photography"

    class Config:
        extra = "allow"
