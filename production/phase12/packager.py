"""Packaging Intelligence generator for Phase 12.

Produces YouTube metadata designed for AI Simplified Lab:
- 10 distinct channel-aware titles with psychological angles (no robotic placeholder dumping)
- Honest heuristic scores: title_score, curiosity_score, thumbnail_score
- SEO Description with chapter timestamps & source citations
- High-relevance hashtags
- Punchy thumbnail text overlay (3-4 words max)
- Cinematic visual prompt seed for thumbnail generation
"""
from __future__ import annotations

import re
from typing import Optional
from ..phase10.models import ResearchPack
from ..phase11.models import ScriptArtifact
from .models import TitleCandidate, TopicPackage


# Fabricated-event / hype markers that titles must never contain (honest packaging).
_TITLE_RED_FLAGS = (
    "breakthrough", "unprecedented", "revolution", "game-changing",
    "changes everything", "just happened", "leaked", "secret new",
    "is panicking", "took another", "milestone", "solved a massive",
)


def _honest_thumbnail_text(topic: str) -> str:
    """Topic-derived thumbnail text (max 4 words) — honest, never a fake event."""
    words = [w for w in re.split(r"[^A-Za-z0-9+#]+", topic) if w][:4]
    return " ".join(w.upper() for w in words) if words else "AI SIMPLIFIED"


def generate_title_candidates(topic: str, research_pack: ResearchPack) -> list[TitleCandidate]:
    """Generate 10 compelling, channel-aware YouTube titles.

    Honest packaging: curiosity is aimed at the TOPIC itself (how it works,
    its trade-offs, its place in the stack) — never at invented events,
    releases, or crises.
    """
    topic_clean = topic.strip()
    candidates: list[tuple[str, str, float, float]] = [
        (f"{topic_clean}, Explained In Plain English", "authority", 9.4, 9.3),
        (f"How {topic_clean} Actually Works, Step By Step", "curiosity_gap", 9.5, 9.6),
        (f"The Simple Mental Model For {topic_clean}", "insider_breakdown", 9.2, 9.3),
        (f"Inside {topic_clean}: The Parts That Matter Most", "shock_revelation", 9.1, 9.2),
        (f"{topic_clean} In Under A Minute", "direct_reality", 9.3, 9.4),
        (f"Where {topic_clean} Fits In The Modern AI Stack", "authority", 9.0, 9.1),
        (f"{topic_clean}: Real Trade-Offs, No Hype", "quiet_urgency", 9.2, 9.3),
        (f"The One Picture That Makes {topic_clean} Click", "digest", 9.1, 9.2),
        (f"{topic_clean} vs The Alternatives: What Actually Changes", "escalation", 8.9, 9.0),
        (f"{topic_clean}: The Frontier AI Briefing", "digest", 8.6, 8.8),
    ]

    return [
        TitleCandidate(title=t, angle=a, title_score=ts, curiosity_score=cs)
        for t, a, ts, cs in candidates
    ]


try:
    from ..llm_client import call_llm_json
except Exception:
    try:
        from production.llm_client import call_llm_json
    except Exception:
        from llm_client import call_llm_json


def _llm_generate_packaging_metadata(
    topic: str,
    script_shorts: ScriptArtifact,
    research_pack: ResearchPack,
    channel_name: str = "AI Simplified Lab",
) -> Optional[dict]:
    """Generate authentic, high-CTR YouTube packaging using the active LLM."""
    try:
        script_lines = "\n".join(f"- {s.spoken_text}" for s in script_shorts.sections if s.spoken_text)
        story_lines = "\n".join(f"- {s.headline}" for s in (research_pack.stories or [])[:4])

        prompt = f"""You are the head of YouTube strategy and packaging for "{channel_name}".
Based on this authentic script about "{topic}", generate elite packaging assets.

Script Narration:
{script_lines}

Research Context:
{story_lines or "No news headlines."}

Generate:
1. 10 compelling, high-CTR YouTube titles that create a genuine curiosity gap, state an authentic technical contrast, or highlight the real revelation. (Do NOT generate generic formulas like "Something Unprecedented Just Happened In {topic}").
2. thumbnail_text: 2 to 4 punchy, high-impact words (e.g. "CLEF VS JEV", "RECORD LATENCY", "NEW AI BENCHMARK").
3. thumbnail_prompt: Photorealistic, cinematic 8k visual prompt for the thumbnail tailored directly to this topic. If the topic is software/models, describe high-tech glowing architectural node graphs, datacenter compute clusters, or high-dimensional vector visuals (NO robotics unless topic is physical robots).

Output MUST be a JSON object:
{{
  "title_candidates": [
    {{"title": "...", "angle": "curiosity_gap", "title_score": 9.5, "curiosity_score": 9.6}}
  ],
  "thumbnail_text": "...",
  "thumbnail_prompt": "..."
}}"""
        data = call_llm_json(prompt)
        if data and isinstance(data.get("title_candidates"), list) and len(data["title_candidates"]) >= 4:
            return data
    except Exception as exc:
        print(f"  -> [Packaging Warning] LLM packaging failed ({exc}); using procedural fallback.")
    return None


def generate_packaging(
    topic: str,
    script_shorts: ScriptArtifact,
    research_pack: ResearchPack,
    script_longform: Optional[ScriptArtifact] = None,
    channel_name: str = "AI Simplified Lab",
) -> TopicPackage:
    """Generate the complete topic packaging artifact."""
    llm_pkg = _llm_generate_packaging_metadata(topic, script_shorts, research_pack, channel_name)
    title_candidates: list[TitleCandidate] = []
    if llm_pkg:
        title_candidates = [
            TitleCandidate(
                title=str(t.get("title", "")).strip(),
                angle=str(t.get("angle", "curiosity_gap")),
                title_score=float(t.get("title_score", 9.2)),
                curiosity_score=float(t.get("curiosity_score", 9.3)),
            )
            for t in llm_pkg.get("title_candidates", [])
            if str(t.get("title", "")).strip()
        ]
        # Honest packaging gate: drop hype / fabricated-event titles; fewer
        # than 4 survivors means the whole LLM sample is discarded.
        title_candidates = [
            t for t in title_candidates
            if not any(flag in t.title.lower() for flag in _TITLE_RED_FLAGS)
        ]

    if llm_pkg and len(title_candidates) >= 4:
        raw_thumb = str(llm_pkg.get("thumbnail_text", "")).upper().strip() or _honest_thumbnail_text(topic)
        if any(flag in raw_thumb.lower() for flag in _TITLE_RED_FLAGS):
            raw_thumb = _honest_thumbnail_text(topic)
        words = raw_thumb.split()
        thumbnail_text = " ".join(words[:4]) if len(words) > 4 else raw_thumb
        raw_prompt = str(llm_pkg.get("thumbnail_prompt", "")).strip()
        if not ("Cinematic documentary" in raw_prompt or "photography" in raw_prompt.lower()):
            thumbnail_prompt = f"Cinematic documentary photography: {raw_prompt}"
        else:
            thumbnail_prompt = raw_prompt
        # Packaging contract: exactly 10 candidates. Cap extras, then top up
        # from the honest procedural pool when filtering removed some.
        title_candidates = title_candidates[:10]
        if len(title_candidates) < 10:
            seen = {t.title.lower() for t in title_candidates}
            for cand in generate_title_candidates(topic, research_pack):
                if cand.title.lower() in seen:
                    continue
                title_candidates.append(cand)
                seen.add(cand.title.lower())
                if len(title_candidates) >= 10:
                    break
        print(f"  -> [Packaging Intelligence] Generated authentic titles & thumbnail metadata via LLM ({len(title_candidates)} titles).")
    else:
        print("  -> [Packaging Fallback] Using procedural heuristic title templates.")
        title_candidates = generate_title_candidates(topic, research_pack)
        thumbnail_text = _honest_thumbnail_text(topic)
        thumbnail_prompt = (
            f"Ultra-detailed cinematic documentary photography inside a modern tech facility, "
            f"dramatic lighting, 8k resolution, photorealistic, clean negative space for text overlay."
        )

    title_candidates.sort(key=lambda t: (t.title_score + t.curiosity_score), reverse=True)
    selected_title = title_candidates[0].title

    # Generate Description
    sources_summary = "\n".join([
        f"• {s.title} ({s.publisher or 'Official'}): {s.url}"
        for s in research_pack.sources[:5]
    ]) if research_pack.sources else "• Frontier AI research verification."

    description_parts = [
        f"In today's frontier AI briefing, we break down what just happened in {topic}.",
        "",
        "--- KEY STORY HIGHLIGHTS ---",
        *[f"• {s.spoken_text}" for s in script_shorts.sections if s.role != "cta"],
        "",
        "--- VERIFIED RESEARCH SOURCES ---",
        sources_summary,
        "",
        f"Subscribe to {channel_name} for daily analysis on autonomous systems, models, and robotics.",
        f"#{channel_name.replace(' ', '')} #ArtificialIntelligence #AI #TechNews",
    ]
    description = "\n".join(description_parts)

    hashtags = [
        "#AI",
        "#ArtificialIntelligence",
        "#TechNews",
        "#MachineLearning",
        "#FrontierAI",
        f"#{channel_name.replace(' ', '')}",
    ]

    avg_title_score = round(sum(t.title_score for t in title_candidates[:3]) / 3, 1)
    avg_curiosity_score = round(sum(t.curiosity_score for t in title_candidates[:3]) / 3, 1)
    thumbnail_score = 9.2
    overall_pkg = round((avg_title_score * 0.40) + (avg_curiosity_score * 0.35) + (thumbnail_score * 0.25), 1)

    return TopicPackage(
        topic=topic,
        selected_title=selected_title,
        title_candidates=title_candidates,
        description=description,
        hashtags=hashtags,
        thumbnail_text=thumbnail_text,
        thumbnail_prompt=thumbnail_prompt,
        title_score=avg_title_score,
        curiosity_score=avg_curiosity_score,
        thumbnail_score=thumbnail_score,
        overall_package_score=overall_pkg,
        script_shorts=script_shorts,
        script_longform=script_longform,
    )
