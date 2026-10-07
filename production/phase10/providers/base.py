"""Abstract base interface for all search providers.

Every provider returns a list of RawSearchResult objects. Evidence
MUST come from actual HTTP retrieval — never from LLM generation.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class RawSearchResult:
    """A single result returned by a search provider."""
    url: str
    title: str
    snippet: str
    publisher: str = ""
    published_at: Optional[str] = None   # ISO-8601 or None if unknown
    retrieved_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    query: str = ""
    provider: str = ""
    source_type: str = "other"  # official | news | paper | social | other


class SearchProvider(ABC):
    """Base class for all search providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable provider name."""
        ...

    @abstractmethod
    def search(
        self,
        query: str,
        *,
        max_results: int = 10,
        freshness: Optional[str] = None,  # e.g. "1d", "7d", "30d"
    ) -> list[RawSearchResult]:
        """Execute a live search query and return raw results.
        
        MUST NOT use an LLM to generate results.
        MUST contact an external service for results.
        Returns an empty list if no results found (not an error).
        Raises SearchProviderError on unrecoverable provider failure.
        """
        ...

    def is_available(self) -> bool:
        """Return True if the provider is configured and reachable."""
        return False


class SearchProviderError(Exception):
    """Raised when a search provider encounters an unrecoverable error."""
    pass


class LiveResearchUnavailableError(Exception):
    """Raised when no live search provider is configured for production use."""
    pass
