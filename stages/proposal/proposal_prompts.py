"""Prompt engineering for Proposal generation.

Enforces:
- 3 materially divergent creative concepts
- Concrete differences in hook, visual metaphor, narrative structure, scene grammar, renderer family
- Forbids trivial variations (such as dark blue cards vs bigger text)
- Supported renderer families and runtimes
"""
from __future__ import annotations

import json
from typing import Any


PROPOSAL_SYSTEM_PROMPT = """You are the Executive Creative Director for AI Simplified Lab.
Your task is to generate 3 GENUINELY DIFFERENT, HIGHLY CREATIVE video concepts for a YouTube Short based on factual research.

CRITICAL QUALITY RULES:
1. Meaningful Diversity: The 3 concepts must not be cosmetic variations of one idea (e.g. Concept A: dark blue cards; Concept B: dark blue cards with bigger text; Concept C: dark blue cards with more animation). That is unacceptable.
2. Distinct Visual Metaphors: Every concept must have an original, concrete visual metaphor.
   GOOD: "AI infrastructure as an expanding industrial power grid with pressure gauges and mechanical assembly"
   GOOD: "AI progress as a classified archival timeline with declassified stamps, dates, and geographic maps"
   GOOD: "AI capability as a neural network coming alive with cascading luminescence and layered zooms"
   BAD: "futuristic tech graphics", "modern AI visuals", "dynamic cards"
3. Divergent Renderer Families: Assign different renderer families where appropriate:
   Available renderer_family: "explainer", "cinematic", "motion_graphics", "documentary", "screen_demo", "hybrid"
4. Valid Runtimes: Assign render_runtime strictly from: "remotion", "hyperframes", "ffmpeg_pil".
5. Composition Mode: Assign strictly from: "templated", "atelier".
6. Output MUST be valid JSON adhering strictly to the proposal_packet schema.
"""


def build_proposal_prompt(
    research_brief_data: dict[str, Any],
    target_duration: float = 35.0,
    platform: str = "youtube_shorts",
) -> str:
    topic = research_brief_data.get("topic", "AI Technology")
    audience = research_brief_data.get("audience", "general_tech")
    facts = research_brief_data.get("facts", [])
    angles = research_brief_data.get("angles_discovered", [])

    facts_summary = []
    for f in facts[:8]:
        if isinstance(f, dict):
            facts_summary.append(f.get("claim", ""))
        elif isinstance(f, str):
            facts_summary.append(f)

    prompt_payload = {
        "topic": topic,
        "audience": audience,
        "platform": platform,
        "target_duration": target_duration,
        "discovered_angles": angles[:4],
        "key_facts": facts_summary,
        "required_output": {
            "concepts": [
                {
                    "concept_id": "concept_01",
                    "title": "Title for Concept 1",
                    "concept_family": "e.g. system_visualization | documentary | analogy_driven",
                    "hook": "Specific, attention-grabbing opening question or observation",
                    "audience_promise": "What viewer learns or experiences",
                    "narrative_structure": "Hook -> Mechanical breakdown -> Climax reveal -> Takeaway",
                    "visual_direction": "Concrete visual style and aesthetic language",
                    "visual_metaphor": "Specific real-world physical or architectural metaphor",
                    "tone": "Urgent and technical",
                    "pacing": "Fast, metric-driven cuts",
                    "scene_grammar": "Split-screen telemetry, HUD diagnostics, macro circuit closeups",
                    "renderer_family": "explainer",
                    "render_runtime": "remotion",
                    "composition_mode": "atelier",
                    "asset_strategy": "vector schematics, live code snippets, synthetic telemetry overlays",
                    "target_duration": target_duration,
                    "reasoning": "Why this angle and metaphor uniquely suits the topic"
                }
            ],
            "selected_concept_id": None
        }
    }

    return (
        f"Generate 3 materially divergent creative concepts for: {topic!r}\n\n"
        f"Research Context:\n{json.dumps(prompt_payload, indent=2)}\n\n"
        "Generate exactly 3 concepts (concept_01, concept_02, concept_03) with distinct hooks, "
        "divergent visual metaphors, different renderer families, and varied scene grammar.\n"
        "Return ONLY a valid JSON object matching the required structure."
    )
