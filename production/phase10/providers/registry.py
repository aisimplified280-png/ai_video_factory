"""Provider registry — selects the best available live search provider."""
from __future__ import annotations

import os
from typing import Optional
from .base import SearchProvider, LiveResearchUnavailableError
from .brave import BraveSearchProvider
from .google_news import GoogleNewsRSSProvider
from .official import OfficialSourcesProvider
from .reddit import RedditProvider
from .multi import MultiProvider


def get_provider(provider_name: Optional[str] = None) -> SearchProvider:
    """Return the requested or default search provider.
    
    If provider_name is specified:
      - "multi" or "all": aggregates Official, Google News RSS, Reddit, and Brave.
      - "google_news": Google News RSS provider (no API key required).
      - "official": Official lab/corporate sources provider.
      - "reddit": Reddit community provider.
      - "brave": Brave Search API.
    
    If provider_name is None, reads SEARCH_PROVIDER env var (defaulting to "brave").
    When "brave" is selected without BRAVE_SEARCH_API_KEY, raises LiveResearchUnavailableError.
    """
    selected = (provider_name or os.getenv("SEARCH_PROVIDER", "brave")).lower().strip()

    if selected in {"multi", "all"}:
        multi = MultiProvider()
        if multi.is_available():
            return multi
        raise LiveResearchUnavailableError("Multi-provider search is not available.")

    if selected == "google_news":
        gn = GoogleNewsRSSProvider()
        if gn.is_available():
            return gn
        raise LiveResearchUnavailableError("Google News RSS provider is not available.")

    if selected == "official":
        off = OfficialSourcesProvider()
        if off.is_available():
            return off
        raise LiveResearchUnavailableError("Official sources provider is not available.")

    if selected == "reddit":
        red = RedditProvider()
        if red.is_available():
            return red
        raise LiveResearchUnavailableError("Reddit provider is not available.")

    if selected == "brave":
        brave = BraveSearchProvider()
        if brave.is_available():
            return brave
        raise LiveResearchUnavailableError(
            "No live search provider is configured. "
            "Set BRAVE_SEARCH_API_KEY to enable live research, "
            "or use --provider multi / --provider google_news. "
            "Research mode will be 'unavailable' until a provider is configured."
        )

    raise ValueError(f"Unknown search provider: {selected}")
