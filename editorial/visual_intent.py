from __future__ import annotations

import re
from typing import Iterable

INTENT_KEYWORDS = {
    "process": ["how", "step", "process", "works", "workflow", "sequence", "then", "next", "pipeline"],
    "transformation": ["turns", "becomes", "changes", "transforms", "evolves", "into", "become"],
    "comparison": ["compare", "versus", "vs", "difference", "before", "after", "better", "worse"],
    "timeline": ["timeline", "history", "first", "later", "then", "years", "before", "after"],
    "hierarchy": ["levels", "layers", "top", "bottom", "rank", "priority", "structure"],
    "network": ["network", "connected", "graph", "nodes", "links", "routes", "system"],
    "connection": ["connect", "match", "pair", "route", "link", "join", "nearby"],
    "workflow": ["workflow", "task", "handoff", "automates", "orchestration", "runs"],
    "cause_effect": ["because", "causes", "drives", "leads", "creates", "results in", "makes"],
    "before_after": ["before", "after", "old", "new", "previous", "today"],
    "growth": ["grow", "growth", "increase", "rise", "scale", "larger", "more"],
    "decline": ["drop", "decline", "fall", "down", "slower", "reduce"],
    "alert": ["warning", "risk", "fail", "error", "issue", "problem", "slow", "break"],
    "discovery": ["find", "discover", "reveal", "learn", "realize", "spot"],
    "interaction": ["click", "use", "interact", "prompt", "chat", "agent", "tool"],
    "system": ["system", "platform", "architecture", "stack", "engine", "service"],
    "architecture": ["architecture", "layers", "components", "stack", "modules", "api"],
    "location": ["in", "at", "location", "map", "region", "city", "country"],
    "statistics": ["percent", "rate", "million", "billion", "stat", "number", "value"],
    "ranking": ["best", "top", "leader", "rank", "highest", "lowest"],
    "quote": ["said", "quote", "says", "commented", "noted"],
    "definition": ["means", "is", "defined", "refers", "called"],
    "list": ["three", "four", "five", "first", "second", "third", "points"],
    "announcement": ["launch", "introduces", "announces", "released", "new", "today", "official"],
    "product": ["product", "feature", "tool", "app", "platform", "experience"],
    "technology": ["ai", "model", "llm", "machine learning", "compute", "data", "cloud"],
    "person": ["person", "user", "team", "manager", "developer"],
    "organization": ["company", "startup", "team", "lab", "company"],
    "abstract_concept": ["idea", "concept", "principle", "theory", "signal"],
}

ENTITY_BLOCKLIST = {
    "the", "and", "for", "with", "from", "into", "that", "this", "what", "when", "where",
    "why", "how", "there", "then", "next", "then", "uber", "openai", "chatgpt", "ai", "lab",
    "simplified", "more", "about", "because", "today", "still"
}


def _tokenize(text: str) -> list[str]:
    return [t.lower() for t in re.findall(r"[A-Za-z][A-Za-z0-9/.-]*", text or "")]


def analyze_narration(text: str) -> dict:
    """Classify narration into one or more semantic intents."""
    lowered = (text or "").lower()
    intents = []
    for name, keywords in INTENT_KEYWORDS.items():
        if any(keyword in lowered for keyword in keywords):
            intents.append(name)
    if not intents:
        intents = ["abstract_concept"]

    # Keep only the most meaningful order, with a stable primary intent.
    ordered = []
    for name in ["announcement", "technology", "process", "comparison", "connection", "network",
                 "workflow", "growth", "alert", "system", "architecture", "statistics",
                 "timeline", "before_after", "cause_effect", "discovery", "interaction"]:
        if name in intents:
            ordered.append(name)
    for name in intents:
        if name not in ordered:
            ordered.append(name)

    primary = ordered[0]
    entities = []
    for match in re.findall(r"\b[A-Z][A-Za-z0-9-]{2,}\b", text or ""):
        value = match.lower()
        if value not in ENTITY_BLOCKLIST and value not in {"ai", "lab", "simplified"}:
            entities.append(match)
    entities = list(dict.fromkeys(entities))[:6]
    relationship = "connects actors and actions"
    if "connection" in ordered or "network" in ordered:
        relationship = "connects separate parts into a working system"
    elif "process" in ordered:
        relationship = "moves through a clear sequence"
    elif "comparison" in ordered:
        relationship = "shows a clear before/after or difference"
    elif "growth" in ordered:
        relationship = "shows expansion or momentum"
    elif "alert" in ordered:
        relationship = "signals a problem or risk"

    return {
        "intents": ordered,
        "primary_intent": primary,
        "entities": entities,
        "relationship": relationship,
        "density": min(4, max(1, len(ordered) + len(entities) // 2)),
    }
