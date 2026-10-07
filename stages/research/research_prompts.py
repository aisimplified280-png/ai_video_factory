"""Prompt templates for research brief synthesis.

Enforces:
- Strict fact-to-source linkage
- Forbids hallucinated URLs or claims
- Structured JSON output matching research_brief schema
"""
from __future__ import annotations

import json
from typing import Sequence
from stages.research.source_collector import SourceRecord


RESEARCH_SYSTEM_PROMPT = """You are the Senior Research Director for AI Simplified Lab.
Your goal is to synthesize rigorous, factual research about a technical AI topic from verified source documents.

CRITICAL RULES:
1. NEVER fabricate or invent URLs, source titles, or author names.
2. For EVERY claim in "facts", you MUST cite the exact "source_ids" (e.g. ["src_001", "src_002"]) from the sources provided.
3. If an interesting fact cannot be supported by the provided source excerpts, DO NOT INCLUDE IT.
4. Distinguish between hard verified facts vs opinions or marketing hype.
5. Structure your output as a single, valid JSON object matching the requested schema.
"""


def build_research_prompt(
    topic: str,
    audience: str,
    platform: str,
    sources: Sequence[SourceRecord],
    depth: str = "standard",
    is_time_sensitive: bool = False,
) -> str:
    """Format user prompt containing topic details and ranked source excerpts."""
    sources_summary = []
    for s in sources:
        sources_summary.append({
            "source_id": s.source_id,
            "title": s.title,
            "url": s.url,
            "domain": s.domain,
            "published_at": s.published_at or "unspecified",
            "content_excerpt": s.content_excerpt[:1200],
        })

    prompt_data = {
        "task": "synthesize_research_brief",
        "topic": topic,
        "audience": audience,
        "platform": platform,
        "research_depth": depth,
        "is_time_sensitive": is_time_sensitive,
        "verified_sources": sources_summary,
        "instructions": (
            "Analyze the verified sources above. Synthesize a structured research brief. "
            "Every item in 'facts' must be an object with: 'claim' (string), 'source_ids' (list of valid source_ids), "
            "and 'confidence' (number 0.0 to 1.0). "
            "Provide at least 3 facts and 2 distinct angles."
        ),
        "expected_json_structure": {
            "topic": topic,
            "audience": audience,
            "content_landscape": "Overview of current discussion and state-of-the-art",
            "facts": [
                {
                    "claim": "Clear factual statement",
                    "source_ids": ["src_001"],
                    "confidence": 0.95
                }
            ],
            "data_points": ["Specific numeric metric or release date"],
            "expert_views": ["Key takeaway or perspective from domain experts"],
            "audience_questions": ["Key question the audience wants answered"],
            "angles_discovered": [
                "Angle 1: Compelling perspective or narrative hook",
                "Angle 2: Counter-intuitive insight or trade-off"
            ],
            "risks": ["Potential limitation, caveat, or technical hurdle"]
        }
    }

    return (
        f"Synthesize a factual Research Brief for the topic: {topic!r}\n\n"
        f"Input Data:\n{json.dumps(prompt_data, indent=2)}\n\n"
        "Return ONLY a valid JSON object matching the expected structure."
    )
