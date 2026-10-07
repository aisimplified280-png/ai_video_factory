"""Multi-source research provider that aggregates across multiple search channels.

Combines:
- OfficialSourcesProvider (Tier 1 corporate/lab announcements)
- GoogleNewsRSSProvider (Tier 2/3 breaking news via RSS)
- RedditProvider (Tier 4 community reactions / leaks)
- BraveSearchProvider (if BRAVE_SEARCH_API_KEY is present)
"""
from __future__ import annotations

from typing import Optional, Sequence
from .base import RawSearchResult, SearchProvider
from .google_news import GoogleNewsRSSProvider
from .official import OfficialSourcesProvider
from .reddit import RedditProvider
from .brave import BraveSearchProvider


class MultiProvider(SearchProvider):
    """Aggregates results across all available search providers."""

    def __init__(self, providers: Optional[Sequence[SearchProvider]] = None) -> None:
        if providers is not None:
            self._providers = list(providers)
        else:
            self._providers = [
                OfficialSourcesProvider(),
                GoogleNewsRSSProvider(),
                RedditProvider(),
            ]
            brave = BraveSearchProvider()
            if brave.is_available():
                self._providers.append(brave)

    @property
    def name(self) -> str:
        return "multi"

    def is_available(self) -> bool:
        return any(p.is_available() for p in self._providers)

    def search(
        self,
        query: str,
        *,
        max_results: int = 10,
        freshness: Optional[str] = None,
    ) -> list[RawSearchResult]:
        aggregated: list[RawSearchResult] = []
        # Query providers with appropriate split
        per_provider = max(3, max_results // max(1, len(self._providers)))

        for provider in self._providers:
            if not provider.is_available():
                continue
            try:
                results = provider.search(
                    query,
                    max_results=per_provider,
                    freshness=freshness,
                )
                aggregated.extend(results)
            except Exception:
                continue

        return aggregated
