"""Story selector and narrative ordering engine for Phase 11.

Identifies the Hook Story (highest shock + virality + trust) to seize viewer
attention in the critical first 3 seconds, and selects the optimal story lineup
for Shorts (Top 3) or Long-Form (Top 5).
"""
from __future__ import annotations

from typing import Sequence
from ..phase10.models import ResearchPack, StoryRecord
from .models import ScriptFormat


def select_stories_for_script(
    research_pack: ResearchPack,
    script_format: ScriptFormat = ScriptFormat.SHORTS,
) -> tuple[StoryRecord, list[StoryRecord]]:
    """Select hook story and narrative story lineup from research pack."""
    candidates = list(research_pack.top_stories or research_pack.stories)
    if not candidates:
        # Create a fallback story from topic if research is empty
        fallback = StoryRecord(
            story_id="story_default",
            headline=f"Major breakthroughs announced in {research_pack.topic}",
            summary=f"New research and engineering milestones released for {research_pack.topic}.",
            trust_score=0.9,
            rank=1,
        )
        return fallback, [fallback]

    # Hook Story: find candidate with maximum combined shock, virality, and trust
    def hook_potential(s: StoryRecord) -> float:
        sc = s.scoring
        return (sc.shock_factor * 0.40) + (sc.virality * 0.35) + (sc.trust_score * 0.25)

    hook_story = max(candidates, key=hook_potential)

    # Narrative lineup: Hook story first, then top remaining ranked stories
    limit = 3 if script_format == ScriptFormat.SHORTS else 5
    remaining = [s for s in candidates if s.story_id != hook_story.story_id]
    
    lineup = [hook_story] + remaining[: limit - 1]
    return hook_story, lineup
