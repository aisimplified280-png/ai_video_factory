"""Reddit search provider for community sentiment, tool discoveries, and leaks.

Queries public AI subreddits (r/singularity, r/artificial, r/MachineLearning, r/OpenAI).
Classified as source_type="social" and Tier 4. Used for buzz and discovery,
never treated as authoritative verification.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
from typing import Optional
from urllib.parse import quote_plus

try:
    import requests
    _REQUESTS_AVAILABLE = True
except ImportError:
    _REQUESTS_AVAILABLE = False

from .base import RawSearchResult, SearchProvider


class RedditProvider(SearchProvider):
    """Fetches community posts and reactions from top AI subreddits."""

    @property
    def name(self) -> str:
        return "reddit"

    def is_available(self) -> bool:
        return _REQUESTS_AVAILABLE

    def search(
        self,
        query: str,
        *,
        max_results: int = 10,
        freshness: Optional[str] = None,
    ) -> list[RawSearchResult]:
        if not self.is_available():
            return []

        # Map freshness to reddit time filter
        time_map = {
            "1d": "day",
            "7d": "week",
            "30d": "month",
            "1y": "year",
        }
        t_param = time_map.get(freshness, "month") if freshness else "all"

        subreddits = "singularity+artificial+MachineLearning+OpenAI+LocalLLaMA"
        url = (
            f"https://www.reddit.com/r/{subreddits}/search.json"
            f"?q={quote_plus(query.strip())}&restrict_sr=1&sort=new&t={t_param}&limit={max_results}"
        )
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AI-Simplified-Video-Factory/1.0"
        }

        try:
            resp = requests.get(url, headers=headers, timeout=8)
            if resp.status_code != 200:
                return []
            data = resp.json()
            return self._parse_json(data, query=query, max_results=max_results)
        except Exception:
            return []

    def _parse_json(self, data: dict, query: str, max_results: int) -> list[RawSearchResult]:
        results: list[RawSearchResult] = []
        children = data.get("data", {}).get("children", [])
        for c in children:
            item = c.get("data", {})
            title = item.get("title", "").strip()
            permalink = item.get("permalink", "")
            if not title or not permalink:
                continue

            full_url = f"https://www.reddit.com{permalink}"
            created_utc = item.get("created_utc")
            published_at = (
                datetime.fromtimestamp(created_utc, timezone.utc).isoformat()
                if created_utc
                else None
            )
            selftext = item.get("selftext", "")[:300]
            subreddit = item.get("subreddit_name_prefixed", "r/reddit")

            results.append(RawSearchResult(
                url=full_url,
                title=title,
                snippet=selftext,
                publisher=subreddit,
                published_at=published_at,
                query=query,
                provider=self.name,
                source_type="social",
            ))

            if len(results) >= max_results:
                break

        return results
