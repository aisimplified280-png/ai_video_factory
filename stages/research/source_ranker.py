"""Source quality ranking and deduplication.

Ranks sources based on:
- authority
- relevance
- recency
- primary-source status
- content completeness

Avoids treating search snippets as full evidence.
"""
from __future__ import annotations

import re
import urllib.parse
from datetime import datetime, timezone
from typing import Sequence

from stages.research.source_collector import SourceRecord, extract_domain


# Known high-authority primary and secondary domains
PRIMARY_DOMAINS = {
    "openai.com", "anthropic.com", "deepmind.google", "ai.googleblog.com",
    "meta.com", "ai.meta.com", "apple.com", "microsoft.com", "arxiv.org",
    "github.com", "huggingface.co", "nist.gov", "whitehouse.gov",
}

REPUTABLE_PUBLICATIONS = {
    "reuters.com", "bloomberg.com", "theverge.com", "wired.com", "technologyreview.com",
    "arstechnica.com", "techcrunch.com", "wsj.com", "ft.com", "nature.com", "science.org"
}


def normalize_url(url: str) -> str:
    """Strip query tracking parameters, hashes, trailing slashes."""
    try:
        parsed = urllib.parse.urlparse(url)
        # Filter out common tracking parameters
        clean_query = []
        if parsed.query:
            qs = urllib.parse.parse_qsl(parsed.query)
            clean_query = [(k, v) for k, v in qs if not k.startswith("utm_") and k not in ("fbclid", "gclid", "ref")]
        clean_qs = urllib.parse.urlencode(clean_query)
        path = parsed.path.rstrip("/")
        return urllib.parse.urlunparse((parsed.scheme.lower(), parsed.netloc.lower(), path, "", clean_qs, ""))
    except Exception:
        return url.strip().lower()


class SourceRanker:
    """Ranks and deduplicates candidate research sources."""

    def __init__(self, topic: str = "", is_time_sensitive: bool = False) -> None:
        self.topic = topic
        self.is_time_sensitive = is_time_sensitive
        self.topic_keywords = self._extract_keywords(topic)

    def _extract_keywords(self, text: str) -> set[str]:
        words = re.findall(r"\b[a-zA-Z0-9_\-]{3,}\b", text.lower())
        stopwords = {"how", "why", "what", "when", "with", "this", "that", "from", "into", "your", "about"}
        return set(words) - stopwords

    def score_source(self, record: SourceRecord) -> float:
        domain = extract_domain(record.url)

        # 1. Authority (0.0 to 1.0)
        authority_score = 0.5
        if domain in PRIMARY_DOMAINS or record.source_type in ("official_announcement", "documentation", "research_paper"):
            authority_score = 1.0
        elif domain in REPUTABLE_PUBLICATIONS or record.source_type == "reputable_publication":
            authority_score = 0.85
        elif record.source_type == "user_direct":
            authority_score = 0.80

        # 2. Primary source status bonus (0.0 or 0.2)
        primary_bonus = 0.2 if authority_score >= 0.9 else 0.0

        # 3. Content completeness (0.0 to 1.0)
        # Search snippets (< 200 chars) are penalized; rich excerpts (> 500 chars) preferred
        length = len(record.content_excerpt.strip())
        if length > 600:
            completeness = 1.0
        elif length > 250:
            completeness = 0.7
        else:
            completeness = 0.35  # snippet-only penalty

        # 4. Relevance: keyword overlap
        searchable_text = f"{record.title} {record.content_excerpt}".lower()
        if self.topic_keywords:
            matched = sum(1 for kw in self.topic_keywords if kw in searchable_text)
            relevance = min(1.0, matched / max(1, len(self.topic_keywords)))
        else:
            relevance = 0.7

        # 5. Recency / Freshness
        recency = 0.5
        if record.published_at:
            try:
                # Parse date if possible
                pub_dt = datetime.fromisoformat(record.published_at.replace("Z", "+00:00"))
                now = datetime.now(timezone.utc)
                age_days = (now - pub_dt).days
                if age_days <= 7:
                    recency = 1.0
                elif age_days <= 30:
                    recency = 0.85
                elif age_days <= 180:
                    recency = 0.6
                else:
                    recency = 0.3
            except Exception:
                recency = 0.5

        # Weighted calculation
        if self.is_time_sensitive:
            # High weight on recency and authority
            final_score = (
                0.30 * authority_score +
                0.25 * recency +
                0.25 * relevance +
                0.20 * completeness +
                primary_bonus
            )
        else:
            # High weight on authority and completeness
            final_score = (
                0.40 * authority_score +
                0.30 * relevance +
                0.20 * completeness +
                0.10 * recency +
                primary_bonus
            )

        return round(min(1.0, final_score), 3)

    def rank_and_deduplicate(self, sources: Sequence[SourceRecord]) -> list[SourceRecord]:
        """Deduplicate by normalized URL or domain+title, and rank by quality score."""
        seen_urls = set()
        seen_titles = set()
        unique: list[SourceRecord] = []

        for src in sources:
            norm_url = normalize_url(src.url)
            norm_title = re.sub(r"\W+", " ", src.title.lower()).strip()
            key = (extract_domain(src.url), norm_title[:40])

            if norm_url in seen_urls or key in seen_titles:
                continue

            seen_urls.add(norm_url)
            seen_titles.add(key)
            unique.append(src)

        # Score and rank
        scored: list[tuple[float, SourceRecord]] = []
        for src in unique:
            sc = self.score_source(src)
            src.relevance_score = sc
            scored.append((sc, src))

        scored.sort(key=lambda pair: pair[0], reverse=True)

        # Re-assign clean sequential source IDs: src_001, src_002...
        ranked: list[SourceRecord] = []
        for idx, (_, src) in enumerate(scored, 1):
            src.source_id = f"src_{idx:03d}"
            ranked.append(src)

        return ranked
