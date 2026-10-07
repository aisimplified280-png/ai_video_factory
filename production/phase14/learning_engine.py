"""Phase 14 Factory Learning System — empirical performance memory and feedback loop.

Stores:
- views
- CTR (%)
- avg watch percentage (%)
- subscribers gained

Learns:
- Which title angles & patterns achieve highest CTR
- Which hook structures retain viewers through the first 3 seconds
- Which visual styles and environments yield highest retention
- Continuous heuristic optimization of Phase 11 & Phase 12 engines
"""
from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from .models import LearningInsights, VideoMetrics, VideoRecord
from ..phase12.models import TitleCandidate

DEFAULT_MEMORY_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "learning" / "factory_memory.json"

# Seed AI Simplified Lab baseline learning data if database is fresh
BASELINE_RECORDS = [
    {
        "production_id": "base_001",
        "topic": "Robotics Warehouse Automation",
        "selected_title": "Robots Just Took Another Human Job",
        "title_angle": "shock_revelation",
        "hook_text": "Warehouse robots are getting smarter fast.",
        "hook_style": "fast_assertion",
        "visual_style": "documentary_industrial",
        "thumbnail_text": "ROBOTS UNLEASHED",
        "metrics": {
            "views": 48200,
            "ctr_percent": 11.2,
            "avg_watch_percentage": 86.4,
            "subscribers_gained": 340,
            "retention_dropoff_3s": 91.5,
        },
        "composite_performance_score": 92.4,
        "recorded_at": "2026-09-15T00:00:00Z",
    },
    {
        "production_id": "base_002",
        "topic": "Autonomous Fleet Coordination",
        "selected_title": "This Warehouse AI Is Learning Too Fast",
        "title_angle": "curiosity_gap",
        "hook_text": "A new AI coordination engine can now direct entire fleets.",
        "hook_style": "fast_assertion",
        "visual_style": "documentary_industrial",
        "thumbnail_text": "LEARNING FAST",
        "metrics": {
            "views": 36500,
            "ctr_percent": 10.4,
            "avg_watch_percentage": 81.2,
            "subscribers_gained": 215,
            "retention_dropoff_3s": 88.0,
        },
        "composite_performance_score": 88.1,
        "recorded_at": "2026-09-22T00:00:00Z",
    },
    {
        "production_id": "base_003",
        "topic": "Frontier AI Hardware",
        "selected_title": "Why Warehouses Are Replacing Humans In 2026",
        "title_angle": "extreme_shift",
        "hook_text": "AI chip engineering just took a massive leap.",
        "hook_style": "fast_assertion",
        "visual_style": "high_contrast_cleanroom",
        "thumbnail_text": "REPLACED 2026",
        "metrics": {
            "views": 29800,
            "ctr_percent": 9.1,
            "avg_watch_percentage": 78.5,
            "subscribers_gained": 180,
            "retention_dropoff_3s": 84.2,
        },
        "composite_performance_score": 82.3,
        "recorded_at": "2026-09-29T00:00:00Z",
    },
]


class FactoryLearningSystem:
    """Manages video performance database and produces learning insights."""

    def __init__(self, memory_path: Path | str | None = None) -> None:
        self.memory_path = Path(memory_path) if memory_path else DEFAULT_MEMORY_PATH
        self.memory_path.parent.mkdir(parents=True, exist_ok=True)
        self.records: list[VideoRecord] = self._load_records()

    def _load_records(self) -> list[VideoRecord]:
        if not self.memory_path.exists():
            # Initialize with seed baseline
            records = [VideoRecord(**r) for r in BASELINE_RECORDS]
            self._save_records(records)
            return records
        try:
            data = json.loads(self.memory_path.read_text("utf-8"))
            return [VideoRecord(**r) for r in data]
        except Exception:
            return [VideoRecord(**r) for r in BASELINE_RECORDS]

    def _save_records(self, records: list[VideoRecord]) -> None:
        self.memory_path.parent.mkdir(parents=True, exist_ok=True)
        data = [r.model_dump() for r in records]
        self.memory_path.write_text(json.dumps(data, indent=2), "utf-8")

    def record_video_metrics(
        self,
        production_id: str,
        topic: str,
        title: str,
        title_angle: str,
        metrics: VideoMetrics,
        hook_text: str = "",
        hook_style: str = "fast_assertion",
        visual_style: str = "documentary_industrial",
        thumbnail_text: str = "",
    ) -> VideoRecord:
        """Store or update real-world performance metrics for a video."""
        # Calculate composite score (0 - 100)
        # Weights: Watch % (45%), CTR (35%), Retention @ 3s (10%), Subscriber conversion (10%)
        score = (
            (metrics.avg_watch_percentage * 0.45)
            + (min(metrics.ctr_percent * 3.5, 35.0))
            + (metrics.retention_dropoff_3s * 0.10)
            + (min(metrics.subscribers_gained * 0.1, 10.0))
        )
        score = round(min(100.0, max(0.0, score)), 1)

        now = datetime.now(timezone.utc).isoformat()
        rec = VideoRecord(
            production_id=production_id,
            topic=topic,
            selected_title=title,
            title_angle=title_angle,
            hook_text=hook_text,
            hook_style=hook_style,
            visual_style=visual_style,
            thumbnail_text=thumbnail_text,
            metrics=metrics,
            composite_performance_score=score,
            recorded_at=now,
        )

        # Update or append
        existing_idx = next((i for i, r in enumerate(self.records) if r.production_id == production_id), None)
        if existing_idx is not None:
            self.records[existing_idx] = rec
        else:
            self.records.append(rec)

        self._save_records(self.records)
        return rec

    def get_learning_insights(self) -> LearningInsights:
        """Synthesize empirical patterns into actionable intelligence."""
        if not self.records:
            return LearningInsights()

        # Angle statistics
        angle_scores = defaultdict(list)
        angle_ctrs = defaultdict(list)
        for r in self.records:
            angle_scores[r.title_angle].append(r.composite_performance_score)
            angle_ctrs[r.title_angle].append(r.metrics.ctr_percent)

        top_angles = []
        for angle, scores in angle_scores.items():
            top_angles.append({
                "angle": angle,
                "count": len(scores),
                "avg_score": round(sum(scores) / len(scores), 1),
                "avg_ctr": round(sum(angle_ctrs[angle]) / len(angle_ctrs[angle]), 1),
            })
        top_angles.sort(key=lambda a: a["avg_score"], reverse=True)

        # Hook pattern statistics
        hook_scores = defaultdict(list)
        for r in self.records:
            hook_scores[r.hook_style].append(r.metrics.avg_watch_percentage)

        top_hooks = []
        for style, w_pcts in hook_scores.items():
            top_hooks.append({
                "style": style,
                "count": len(w_pcts),
                "avg_watch_percentage": round(sum(w_pcts) / len(w_pcts), 1),
            })
        top_hooks.sort(key=lambda h: h["avg_watch_percentage"], reverse=True)

        # Visual style statistics
        vis_scores = defaultdict(list)
        for r in self.records:
            vis_scores[r.visual_style].append(r.metrics.avg_watch_percentage)

        top_vis = []
        for vstyle, w_pcts in vis_scores.items():
            top_vis.append({
                "visual_style": vstyle,
                "count": len(w_pcts),
                "avg_retention": round(sum(w_pcts) / len(w_pcts), 1),
            })
        top_vis.sort(key=lambda v: v["avg_retention"], reverse=True)

        # Winning keywords from top-scoring titles
        high_performers = [r for r in self.records if r.composite_performance_score >= 80.0]
        words = defaultdict(int)
        for r in high_performers:
            for w in r.selected_title.split():
                w_clean = w.strip(",.!?\"'").lower()
                if len(w_clean) > 3 and w_clean not in {"this", "that", "with", "from", "your", "what"}:
                    words[w_clean] += 1
        winning_words = [w for w, c in sorted(words.items(), key=lambda x: x[1], reverse=True)[:8]]

        recommended_angles = [a["angle"] for a in top_angles if a["avg_ctr"] >= 9.0]
        if not recommended_angles:
            recommended_angles = ["shock_revelation", "curiosity_gap"]

        return LearningInsights(
            total_videos_analyzed=len(self.records),
            top_title_angles=top_angles,
            top_hook_patterns=top_hooks,
            top_visual_styles=top_vis,
            winning_keywords=winning_words,
            underperforming_patterns=["release_notes_ticker", "passive_academic_questions"],
            recommended_title_angles=recommended_angles,
            recommended_visual_direction="cinematic documentary photography, industrial tech, high contrast",
        )

    def apply_learned_title_boosts(
        self, candidates: list[TitleCandidate]
    ) -> list[TitleCandidate]:
        """Apply empirical heuristic boosts to title candidates based on historical data."""
        insights = self.get_learning_insights()
        best_angles = {a["angle"]: a["avg_ctr"] for a in insights.top_title_angles}
        winning_kw = set(insights.winning_keywords)

        boosted: list[TitleCandidate] = []
        for c in candidates:
            score = c.title_score
            curiosity = c.curiosity_score

            # Angle boost: if angle historically performed with >10% CTR, boost by +0.3
            hist_ctr = best_angles.get(c.angle, 8.0)
            if hist_ctr >= 10.5:
                score += 0.3
                curiosity += 0.2
            elif hist_ctr < 8.0:
                score -= 0.3

            # Keyword match boost: +0.2 for containing top-performing vocabulary
            title_lower = c.title.lower()
            if any(kw in title_lower for kw in winning_kw):
                score += 0.2
                curiosity += 0.2

            score = round(min(10.0, max(1.0, score)), 1)
            curiosity = round(min(10.0, max(1.0, curiosity)), 1)

            boosted.append(TitleCandidate(
                title=c.title,
                angle=c.angle,
                title_score=score,
                curiosity_score=curiosity,
            ))

        # Re-sort descending by composite score
        boosted.sort(key=lambda x: (x.title_score + x.curiosity_score), reverse=True)
        return boosted


def get_learning_system() -> FactoryLearningSystem:
    return FactoryLearningSystem()
