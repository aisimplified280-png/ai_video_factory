"""Query expander: generates multiple targeted search queries from a topic.

Query GENERATION may use simple heuristics or an LLM.
The evidence itself must NEVER come from the LLM — only from retrieved sources.
"""
from __future__ import annotations

# Source priority keyword expansion — no LLM needed for basic expansion
_TIER1_ORGS = ["OpenAI", "Anthropic", "Google DeepMind", "Meta AI", "Microsoft", "NVIDIA", "Hugging Face"]


def expand_queries(topic: str, max_queries: int = 6) -> list[str]:
    """Generate multiple targeted search queries for a topic.
    
    Produces a diversity of query formulations to maximize source coverage:
    - Broad query
    - Official source queries (site: operators)
    - Specific entity + action queries
    - Date-anchored queries
    """
    queries: list[str] = []
    topic_stripped = topic.strip()

    # 1. Base query
    queries.append(topic_stripped)

    # 2. News-oriented query
    queries.append(f"{topic_stripped} announcement 2026")

    # 3. Official domain queries for Tier 1 sources (pick most likely matches)
    topic_lower = topic_stripped.lower()
    if "openai" in topic_lower or "gpt" in topic_lower or "chatgpt" in topic_lower or "astra" in topic_lower:
        queries.append(f"site:openai.com {topic_stripped}")
    if "anthropic" in topic_lower or "claude" in topic_lower:
        queries.append(f"site:anthropic.com {topic_stripped}")
    if "google" in topic_lower or "gemini" in topic_lower or "deepmind" in topic_lower:
        queries.append(f"site:deepmind.google {topic_stripped}")
    if "meta" in topic_lower or "llama" in topic_lower:
        queries.append(f"site:ai.meta.com {topic_stripped}")

    # 4. Research/paper query
    queries.append(f"{topic_stripped} research paper arxiv")

    # 5. Reuters/AP for news verification
    queries.append(f"{topic_stripped} Reuters OR \"Associated Press\"")

    # De-duplicate and cap
    seen: set[str] = set()
    unique: list[str] = []
    for q in queries:
        if q not in seen:
            seen.add(q)
            unique.append(q)
        if len(unique) >= max_queries:
            break

    return unique
