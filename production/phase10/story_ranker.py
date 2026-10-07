"""Story ranker and Top-N selection engine for Phase 10 research.

Scores candidate news stories by:
- virality (buzz, social velocity, leaks)
- subscriber_potential (relevance to YouTube tech audience, major milestones)
- shock_factor (dramatic shifts, unprecedented benchmarks, disruptive claims)
- visual_potential (physical machinery, robots, hardware vs abstract concepts)
- trust_score (corroboration by Tier-1/Tier-2 sources)

Outputs ranked stories and selects Top 5 stories of the week.
"""
from __future__ import annotations

import re
from typing import Sequence
from .models import ClaimRecord, SourceRecord, StoryRecord, StoryScoring
from .visual_extractor import extract_visual_facts

VIRALITY_KEYWORDS = {
    "leak", "leaked", "secret", "viral", "unreleased", "insider", "breaking",
    "exclusive", "rumor", "internal", "stealth", "first look", "surprise"
}

SUBSCRIBER_KEYWORDS = {
    "announces", "launches", "releases", "benchmark", "frontier", "next-gen",
    "architecture", "open source", "free", "upgrade", "autonomous", "agent",
    "capabilities", "superintelligence", "agi", "pricing"
}

SHOCK_KEYWORDS = {
    "shocking", "massive", "unprecedented", "replaces", "crushes", "destroys",
    "beats", "kills", "lawsuit", "ban", "breach", "warning", "flaw", "dethrones",
    "catastrophic", "10x", "100x"
}

PHYSICAL_VISUAL_KEYWORDS = {
    "robot", "arm", "humanoid", "hardware", "chip", "datacenter", "wafer",
    "factory", "facility", "cluster", "gpu", "rack", "sensor", "physical"
}


def rank_stories(
    topic: str,
    sources: Sequence[SourceRecord],
    claims: Sequence[ClaimRecord],
    top_n: int = 5,
) -> tuple[list[StoryRecord], list[StoryRecord]]:
    """Rank stories derived from claims and sources.
    
    Returns (all_stories, top_stories).
    """
    sources_by_id = {s.source_id: s for s in sources}
    candidate_stories: list[StoryRecord] = []

    # If no claims but sources exist, create synthetic candidate items from sources
    items: list[tuple[str, str, list[str], Optional[str]]] = []
    if claims:
        for c in claims:
            items.append((c.claim, c.notes, c.source_ids, c.primary_source_id))
    else:
        for s in sources:
            items.append((s.title, s.snippet, [s.source_id], s.source_id))

    for i, (headline, summary, source_ids, primary_id) in enumerate(items):
        text_lower = (headline + " " + summary).lower()
        words = set(re.findall(r"\b\w+\b", text_lower))

        # 1. Trust Score
        story_sources = [sources_by_id[sid] for sid in source_ids if sid in sources_by_id]
        if any(s.tier == 1 for s in story_sources):
            base_trust = 0.95
        elif any(s.tier == 2 for s in story_sources):
            base_trust = 0.80
        elif any(s.tier == 3 for s in story_sources):
            base_trust = 0.60
        elif any(s.tier == 4 for s in story_sources):
            base_trust = 0.35
        else:
            base_trust = 0.50

        # Boost trust if corroborated by multiple unique publishers
        unique_publishers = {s.publisher for s in story_sources if s.publisher}
        if len(unique_publishers) >= 2:
            base_trust = min(1.0, base_trust + 0.10)
        trust_score = round(base_trust, 2)

        # 2. Topic Semantic Relevance Score (Phase 10.5 Audit Fix)
        # Tokenize topic into meaningful keywords (excluding stop words)
        stop_words = {"and", "the", "for", "with", "from", "that", "this", "our", "are", "was", "will"}
        topic_tokens = {w for w in re.findall(r"\b\w{3,}\b", topic.lower()) if w not in stop_words}
        matched_tokens = topic_tokens.intersection(words)

        if topic_tokens:
            overlap_ratio = len(matched_tokens) / len(topic_tokens)
            # Full match or near full match -> 0.85 - 1.0, partial -> 0.4 - 0.7, zero -> 0.05 penalty
            if matched_tokens:
                relevance = min(1.0, 0.40 + (0.60 * overlap_ratio))
            else:
                relevance = 0.05  # Severe penalty for irrelevant topics
        else:
            relevance = 0.50
        relevance = round(relevance, 2)

        # 3. Virality Score
        virality_hits = len(words.intersection(VIRALITY_KEYWORDS))
        has_social = any(s.tier == 4 or "reddit" in s.url.lower() for s in story_sources)
        virality = min(1.0, 0.40 + (0.20 * virality_hits) + (0.15 if has_social else 0.0))
        virality = round(virality, 2)

        # 4. Subscriber Potential
        sub_hits = len(words.intersection(SUBSCRIBER_KEYWORDS))
        sub_potential = min(1.0, 0.45 + (0.15 * sub_hits))
        sub_potential = round(sub_potential, 2)

        # 5. Shock Factor
        shock_hits = len(words.intersection(SHOCK_KEYWORDS))
        shock_factor = min(1.0, 0.25 + (0.25 * shock_hits))
        shock_factor = round(shock_factor, 2)

        # 6. Visual Potential
        visual_hits = len(words.intersection(PHYSICAL_VISUAL_KEYWORDS))
        visual_potential = min(1.0, 0.40 + (0.20 * visual_hits))
        visual_potential = round(visual_potential, 2)

        # 7. Overall Weighted Score:
        # Trust 30%, Relevance 30%, Visual 20%, Shock 10%, Virality 10%
        overall = round(
            (trust_score * 0.30)
            + (relevance * 0.30)
            + (visual_potential * 0.20)
            + (shock_factor * 0.10)
            + (virality * 0.10),
            3
        )

        scoring = StoryScoring(
            relevance=relevance,
            virality=virality,
            subscriber_potential=sub_potential,
            shock_factor=shock_factor,
            visual_potential=visual_potential,
            trust_score=trust_score,
            overall_score=overall,
        )

        dummy_claim = ClaimRecord(
            claim_id=f"c_{i+1}",
            claim=headline,
            status="CONFIRMED" if trust_score >= 0.8 else "LIKELY",
            confidence=trust_score,
            source_ids=source_ids,
        )
        visual_facts = extract_visual_facts(headline, story_sources, [dummy_claim])

        candidate_stories.append(StoryRecord(
            story_id=f"story_{i+1:03d}",
            headline=headline,
            summary=summary,
            source_ids=source_ids,
            primary_source_id=primary_id,
            trust_score=trust_score,
            visual_facts=visual_facts,
            scoring=scoring,
            rank=0,
        ))

    # Sort descending by overall_score
    candidate_stories.sort(key=lambda s: s.scoring.overall_score, reverse=True)

    # Assign ranks
    for rank_idx, s in enumerate(candidate_stories, start=1):
        s.rank = rank_idx

    top_stories = candidate_stories[:top_n]
    return candidate_stories, top_stories
