"""Intent classification and entity extraction for script sections.

Enforces strict intent limits (1 primary, max 2 secondary intents) to avoid
keyword explosion, and cleanly separates entities, keywords, and emphasis words.
"""
from __future__ import annotations

import re
from typing import Any
from pydantic import BaseModel, Field

VALID_PRIMARY_INTENTS: set[str] = {
    "explain",
    "compare",
    "reveal",
    "warn",
    "show_scale",
    "show_growth",
    "show_cause_effect",
    "show_process",
    "show_history",
    "show_transformation",
    "show_evidence",
    "show_interface",
    "show_system",
    "humanize",
    "conclude",
}

ROLE_DEFAULT_PRIMARY_INTENTS: dict[str, str] = {
    "hook": "reveal",
    "context": "explain",
    "problem": "warn",
    "tension": "warn",
    "mechanism": "show_process",
    "process": "show_process",
    "evidence": "show_evidence",
    "proof": "show_evidence",
    "reveal": "reveal",
    "payoff": "explain",
    "implication": "show_scale",
    "cta": "conclude",
    "transition": "show_transformation",
}


class SemanticIntent(BaseModel):
    """Constrained semantic intent container."""
    primary_intent: str
    secondary_intents: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class ExtractedEntities(BaseModel):
    """Separated entity and emphasis container."""
    primary_subject: str
    entities: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    emphasis_words: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


def classify_intent(
    narrative_role: str,
    spoken_text: str,
    explicit_primary: str | None = None,
    explicit_secondary: list[str] | None = None,
) -> tuple[str, list[str]]:
    """Determine exactly 1 primary intent and 0-2 secondary intents.

    Guarantees no keyword explosion: total intents <= 3.
    """
    text_lower = spoken_text.lower()

    # 1. Primary intent selection
    if explicit_primary and explicit_primary in VALID_PRIMARY_INTENTS:
        primary = explicit_primary
    else:
        # Heuristic based on text & role
        if any(w in text_lower for w in ["exploded", "grew", "scale", "massive", "exponential", "trillion"]):
            primary = "show_scale"
        elif any(w in text_lower for w in ["history", "started in", "years ago", "origin", "founded", "began"]):
            primary = "show_history"
        elif any(w in text_lower for w in ["how it works", "steps", "pipeline", "coordinates", "assembles"]):
            primary = "show_process"
        elif any(w in text_lower for w in ["because", "causes", "leads to", "drives", "triggers"]):
            primary = "show_cause_effect"
        elif any(w in text_lower for w in ["data", "benchmark", "numbers", "study", "evidence", "proven"]):
            primary = "show_evidence"
        elif any(w in text_lower for w in ["subscribe", "follow", "watch next", "comment"]):
            primary = "conclude"
        else:
            primary = ROLE_DEFAULT_PRIMARY_INTENTS.get(narrative_role.lower(), "explain")

    # 2. Secondary intents selection (max 2)
    secondaries: list[str] = []
    if explicit_secondary:
        for s in explicit_secondary:
            s_clean = s.strip().lower()
            if s_clean in VALID_PRIMARY_INTENTS and s_clean != primary and s_clean not in secondaries:
                secondaries.append(s_clean)
                if len(secondaries) >= 2:
                    break

    # If secondaries empty, infer at most 1-2 based on keywords
    if len(secondaries) < 2:
        candidate_checks = [
            ("show_scale", ["power", "compute", "billion", "model"]),
            ("show_system", ["architecture", "agents", "network", "nodes", "graph"]),
            ("show_transformation", ["shifts", "becomes", "transforms", "expands"]),
            ("explain", ["means", "defined", "is essentially"]),
        ]
        for candidate, kws in candidate_checks:
            if candidate != primary and candidate not in secondaries:
                if any(kw in text_lower for kw in kws):
                    secondaries.append(candidate)
                    if len(secondaries) >= 2:
                        break

    return primary, secondaries[:2]


def extract_entities_and_emphasis(
    spoken_text: str,
    primary_subject_hint: str = "",
    emphasis_hint: list[str] | None = None,
    entities_hint: list[str] | None = None,
    keywords_hint: list[str] | None = None,
) -> ExtractedEntities:
    """Extract and strictly separate entities, keywords, and emphasis words.

    RULE: Emphasis words must NEVER be placed in entities!
    """
    # 1. Identify emphasis words (uppercase words of 2+ chars or explicit cues)
    emphasis_words_set: set[str] = set()

    # Find ALL-CAPS words in original text (e.g. "MORE", "EXPLODED")
    raw_tokens = re.findall(r"\b[A-Z]{2,}\b", spoken_text)
    for tok in raw_tokens:
        if tok not in {"AI", "LLM", "GPU", "TPU", "API", "USA", "CEO", "CTA"}:
            emphasis_words_set.add(tok)

    if emphasis_hint:
        for eh in emphasis_hint:
            cleaned_eh = eh.strip()
            if cleaned_eh:
                emphasis_words_set.add(cleaned_eh.upper())

    emphasis_words = sorted(list(emphasis_words_set))
    emphasis_lower_set = {w.lower() for w in emphasis_words}

    # 2. Extract or resolve entities
    resolved_entities: list[str] = []
    if entities_hint:
        for ent in entities_hint:
            ent_clean = ent.strip()
            # Hard Rule: Do NOT treat emphasis words as entities!
            if ent_clean and ent_clean.lower() not in emphasis_lower_set and ent_clean not in resolved_entities:
                resolved_entities.append(ent_clean)

    if not resolved_entities:
        # Heuristic extraction of noun-phrases / capitalized terms
        candidates = re.findall(r"\b(?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*|[A-Z]{2,})\b", spoken_text)
        for c in candidates:
            c_clean = c.strip()
            if c_clean.lower() not in emphasis_lower_set and c_clean not in resolved_entities:
                resolved_entities.append(c_clean)

    # 3. Resolve primary subject
    primary_subject = primary_subject_hint.strip()
    if not primary_subject:
        if resolved_entities:
            primary_subject = resolved_entities[0]
        else:
            primary_subject = "AI Technology"

    # Ensure primary subject is in entities if not an emphasis word
    if primary_subject and primary_subject.lower() not in emphasis_lower_set:
        if primary_subject not in resolved_entities:
            resolved_entities.insert(0, primary_subject)

    # 4. Resolve keywords
    resolved_keywords: list[str] = []
    if keywords_hint:
        for kw in keywords_hint:
            kw_clean = kw.strip().lower()
            if kw_clean and kw_clean not in resolved_keywords:
                resolved_keywords.append(kw_clean)

    if not resolved_keywords:
        # Simple extraction of prominent words > 4 chars not in stop words
        stop_words = {"about", "their", "there", "which", "would", "could", "should", "every", "these", "those"}
        words = re.findall(r"\b[a-zA-Z]{5,}\b", spoken_text.lower())
        for w in words:
            if w not in stop_words and w not in resolved_keywords:
                resolved_keywords.append(w)
            if len(resolved_keywords) >= 5:
                break

    return ExtractedEntities(
        primary_subject=primary_subject,
        entities=resolved_entities,
        keywords=resolved_keywords[:5],
        emphasis_words=emphasis_words,
    )
