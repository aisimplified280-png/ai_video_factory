"""Brave Search API provider.

Requires BRAVE_SEARCH_API_KEY in environment.
Free tier: 2000 queries/month at no cost.
Docs: https://api.search.brave.com/app/documentation/web-search/get-started
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Optional

try:
    import requests
    _REQUESTS_AVAILABLE = True
except ImportError:
    _REQUESTS_AVAILABLE = False

from .base import RawSearchResult, SearchProvider, SearchProviderError

_BRAVE_ENDPOINT = "https://api.search.brave.com/res/v1/web/search"

# Source-type heuristics based on domain patterns
_OFFICIAL_DOMAINS = {
    "openai.com", "anthropic.com", "deepmind.google", "ai.google",
    "ai.meta.com", "microsoft.com", "nvidia.com", "huggingface.co",
    "github.com", "arxiv.org", "research.google",
}
_NEWS_DOMAINS = {
    "reuters.com", "apnews.com", "bloomberg.com", "ft.com",
    "techcrunch.com", "theverge.com", "arstechnica.com", "venturebeat.com",
    "wired.com", "zdnet.com", "engadget.com",
}
_SOCIAL_DOMAINS = {"twitter.com", "x.com", "reddit.com", "threads.net"}


def _infer_source_type(url: str) -> str:
    from urllib.parse import urlparse
    try:
        host = urlparse(url).hostname or ""
        # strip leading www.
        host = host.removeprefix("www.")
        if any(host == d or host.endswith("." + d) for d in _OFFICIAL_DOMAINS):
            return "official"
        if any(host == d or host.endswith("." + d) for d in _NEWS_DOMAINS):
            return "news"
        if any(host == d or host.endswith("." + d) for d in _SOCIAL_DOMAINS):
            return "social"
        return "other"
    except Exception:
        return "other"


def _freshness_to_brave(freshness: Optional[str]) -> Optional[str]:
    """Convert our freshness string to Brave's freshness parameter."""
    if not freshness:
        return None
    mapping = {"1d": "pd", "7d": "pw", "30d": "pm", "1y": "py"}
    return mapping.get(freshness)


class BraveSearchProvider(SearchProvider):
    """Live Brave Search API provider."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        self._api_key = api_key or os.getenv("BRAVE_SEARCH_API_KEY", "")

    @property
    def name(self) -> str:
        return "brave_search"

    def is_available(self) -> bool:
        return bool(self._api_key) and _REQUESTS_AVAILABLE

    def search(
        self,
        query: str,
        *,
        max_results: int = 10,
        freshness: Optional[str] = None,
    ) -> list[RawSearchResult]:
        if not self._api_key:
            raise SearchProviderError("BRAVE_SEARCH_API_KEY not configured")
        if not _REQUESTS_AVAILABLE:
            raise SearchProviderError("'requests' package not installed")

        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": self._api_key,
        }
        params: dict = {"q": query, "count": min(max_results, 20)}
        fresh = _freshness_to_brave(freshness)
        if fresh:
            params["freshness"] = fresh

        try:
            response = requests.get(_BRAVE_ENDPOINT, headers=headers, params=params, timeout=15)
            response.raise_for_status()
        except Exception as exc:
            raise SearchProviderError(f"Brave Search request failed: {exc}") from exc

        retrieved_at = datetime.now(timezone.utc).isoformat()
        results: list[RawSearchResult] = []
        data = response.json()

        for item in data.get("web", {}).get("results", [])[:max_results]:
            url = item.get("url", "")
            # Extract publisher from meta_url or profile
            publisher = (item.get("profile", {}) or {}).get("name", "") or \
                        (item.get("meta_url", {}) or {}).get("netloc", "")
            # Extract publication date from age field or page_age
            published_at = item.get("page_age") or item.get("age")
            
            results.append(RawSearchResult(
                url=url,
                title=item.get("title", ""),
                snippet=item.get("description", ""),
                publisher=publisher,
                published_at=published_at,
                retrieved_at=retrieved_at,
                query=query,
                provider=self.name,
                source_type=_infer_source_type(url),
            ))

        return results
