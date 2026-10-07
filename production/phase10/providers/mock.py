"""Mock search provider for deterministic unit tests.

NEVER used in production. Raises LiveResearchUnavailableError if
invoked outside of an explicit test context.
"""
from __future__ import annotations

from typing import Optional

from .base import RawSearchResult, SearchProvider, LiveResearchUnavailableError


class MockSearchProvider(SearchProvider):
    """Deterministic provider for tests only.
    
    Usage:
        provider = MockSearchProvider(results=[...])
        # Always returns the pre-configured results.
    
    Production guard:
        If allow_in_production=False (default), raises
        LiveResearchUnavailableError in non-test contexts.
    """

    def __init__(
        self,
        results: list[RawSearchResult] | None = None,
        allow_in_production: bool = False,
    ) -> None:
        self._results = results or []
        self._allow_in_production = allow_in_production

    @property
    def name(self) -> str:
        return "mock"

    def is_available(self) -> bool:
        # Available in test contexts only
        return self._allow_in_production or _is_test_context()

    def search(
        self,
        query: str,
        *,
        max_results: int = 10,
        freshness: Optional[str] = None,
    ) -> list[RawSearchResult]:
        if not self._allow_in_production and not _is_test_context():
            raise LiveResearchUnavailableError(
                "MockSearchProvider must not be used in production. "
                "Configure a real search provider (e.g. BRAVE_SEARCH_API_KEY)."
            )
        return [r for r in self._results if r.query == query or not r.query][:max_results]


def _is_test_context() -> bool:
    """Detect if we're running under pytest."""
    try:
        import sys
        return "pytest" in sys.modules or any("pytest" in arg for arg in sys.argv)
    except Exception:
        return False
