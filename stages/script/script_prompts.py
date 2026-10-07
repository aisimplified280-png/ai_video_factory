"""Prompts and prompt builders for script generation.

Enforces hook discipline, retention pacing, visual intent questions,
natural spoken English for TTS, and mandatory CTA section.
"""
from __future__ import annotations

import json
from typing import Any

SCRIPT_SYSTEM_PROMPT = """You are the Senior Editorial Script Director for AI Simplified Lab.
Your task is to write a high-retention, spoken-word vertical video script (30-60 seconds, target 45 seconds).

CRITICAL SCRIPTWRITING RULES:
1. HOOK DISCIPLINE:
   - The opening line MUST create immediate curiosity, tension, surprise, or a provocative question.
   - FORBIDDEN OPENINGS (automatic rejection):
     * "Today we're going to discuss..."
     * "Today we are looking at..."
     * "Artificial intelligence is changing..."
     * "In this video, we will explore..."
     * "Let's take a look at..."
     * "Have you ever wondered..."
   - Open in medias res with a startling fact, stark contrast, or high-stakes mechanism.

2. SPOKEN LANGUAGE FOR TTS:
   - Write exclusively in clear, direct spoken English.
   - Keep sentences punchy and easy to dub. Avoid complex subordinate clauses.
   - Do NOT write visual cues or stage directions into the spoken narration text itself.
   - Target total word count: 105 to 140 words (~2.6 words/sec = 40-52s).

3. NARRATIVE PROGRESSION (NARRATIVE ROLES):
   Every section must have an explicit role from:
   - "hook" (opening punch)
   - "context" or "problem" (the conflict or mystery)
   - "mechanism" or "process" (how it works)
   - "evidence" or "proof" (hard facts/data from research)
   - "reveal" or "payoff" (the insight/climax)
   - "implication" (what this changes)
   - "cta" (final closing section)

4. VISUAL QUESTION REQUIREMENT:
   For every single section, you MUST answer:
   "visual_intent": "What can the viewer SEE that they could not understand from the narration alone?"
   - Rejection rule: If the visual intent is merely "headline and supporting text" or "floating cards", it will be rejected.
   - Visual intent must describe tangible physical actions, spatial shifts, or visual metaphors from art direction.

5. CTA REQUIREMENT:
   - The FINAL section MUST have narrative_role = "cta".
   - Spoken text: "Subscribe to AI Simplified Lab for more AI breakdowns like this."
   - Visual intent: Clean channel brand mark with kinetic subscriber cue.

6. PROMPT OUTPUT FORMAT:
   Return valid JSON with no markdown formatting:
   {
     "title": "Clear punchy title",
     "hook": "The opening sentence",
     "target_duration_seconds": 45.0,
     "audience": "Developers, AI researchers, and tech enthusiasts",
     "sections": [
       {
         "section_id": "sec_01",
         "narrative_role": "hook",
         "spoken_text": "...",
         "emphasis_words": ["KEYWORD1", "KEYWORD2"],
         "visual_intent": "...",
         "pause_after": 0.3,
         "primary_intent": "reveal",
         "secondary_intents": ["show_scale"],
         "primary_subject": "...",
         "entities": ["..."],
         "keywords": ["..."]
       }
     ]
   }
"""


def build_script_prompt(
    topic: str,
    research_brief: dict[str, Any],
    selected_concept: dict[str, Any],
    art_direction: dict[str, Any] | None = None,
    target_duration: float = 45.0,
) -> str:
    """Build user prompt for script generation combining research, concept, and art direction."""
    # Extract facts from research brief
    facts = research_brief.get("facts", [])
    facts_summary = []
    for f in facts[:6]:
        if isinstance(f, dict):
            facts_summary.append(f"- {f.get('claim', '')} (sources: {', '.join(f.get('source_ids', []))})")
        else:
            facts_summary.append(f"- {f}")

    data_points = research_brief.get("data_points", [])
    angles = research_brief.get("angles_discovered", [])

    # Extract concept details
    concept_title = selected_concept.get("title", "")
    concept_hook = selected_concept.get("hook", "")
    visual_metaphor = selected_concept.get("visual_metaphor", "")
    narrative_structure = selected_concept.get("narrative_structure", "")
    tone = selected_concept.get("tone", "urgent and analytical")

    # Extract art direction details if available
    ad_metaphor = ""
    anti_patterns = []
    signature_device = ""
    if art_direction:
        ad_metaphor = art_direction.get("visual_metaphor", "")
        anti_patterns = art_direction.get("anti_patterns", [])
        signature_device = art_direction.get("signature_device", "")

    effective_metaphor = ad_metaphor or visual_metaphor or "System architecture in action"

    return f"""TOPIC: {topic}
TARGET DURATION: {target_duration} seconds (~115-135 words)

SELECTED CREATIVE CONCEPT:
- Title: {concept_title}
- Hook Idea: {concept_hook}
- Tone: {tone}
- Narrative Structure: {narrative_structure}
- Visual Metaphor: {effective_metaphor}

RESEARCH EVIDENCE TO INTEGRATE:
Facts:
{chr(10).join(facts_summary) if facts_summary else "- Key technological mechanisms and benchmarks"}

Data Points:
{json.dumps(data_points, indent=2) if data_points else "[]"}

Angles:
{json.dumps(angles, indent=2) if angles else "[]"}

ART DIRECTION CONSTRAINTS:
- Visual Metaphor: {effective_metaphor}
- Signature Device: {signature_device or 'Dynamic telemetry trail'}
- Forbidden Anti-Patterns: {json.dumps(anti_patterns) if anti_patterns else '["no floating cards every scene", "no text-only slides"]'}

INSTRUCTIONS:
Write a 5 to 7 beat script where each section pushes understanding forward.
Ensure the visual question for every beat provides a clear visual anchor that complements the spoken words.
End with the exact CTA beat specified.
"""
