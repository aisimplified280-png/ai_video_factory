"""Real source collection interface, models, and provider implementations.

Do NOT fabricate sources.
Do NOT insert fake URLs.
If no search provider is configured and external research is required,
the provider must explicitly report RESEARCH_PROVIDER_UNAVAILABLE.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Any, Protocol, runtime_checkable
from pydantic import BaseModel, Field


class SourceRecord(BaseModel):
    """Normalized, deduplicated source record."""
    source_id: str
    title: str
    url: str
    domain: str
    published_at: str | None = None
    retrieved_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    source_type: str = "web_article"
    author: str | None = None
    content_excerpt: str
    relevance_score: float = 0.0
    publisher: str | None = None
    raw_content_path: str | None = None
    summary: str = ""

    model_config = {"extra": "ignore"}


@runtime_checkable
class ResearchSourceProvider(Protocol):
    """Provider-agnostic interface for real research source collection."""

    def is_available(self) -> bool:
        """Return True if the provider is configured and reachable."""
        ...

    def search(self, query: str, limit: int = 5) -> list[SourceRecord]:
        """Search the web or external repository for sources."""
        ...

    def fetch(self, url: str, timeout: int = 15) -> str:
        """Fetch raw HTML or text from a URL."""
        ...

    def extract_content(self, url: str, timeout: int = 15) -> SourceRecord | None:
        """Extract a normalized SourceRecord from a URL."""
        ...


def extract_domain(url: str) -> str:
    """Extract clean domain name from URL."""
    try:
        parsed = urllib.parse.urlparse(url)
        netloc = parsed.netloc.lower()
        if netloc.startswith("www."):
            netloc = netloc[4:]
        return netloc
    except Exception:
        return "unknown"


def clean_html_to_text(html: str) -> str:
    """Basic extraction of readable text from HTML without heavy dependencies."""
    # Remove script and style tags
    text = re.sub(r"<(script|style|noscript)[^>]*>.*?</\1>", " ", html, flags=re.DOTALL | re.IGNORECASE)
    # Remove tags
    text = re.sub(r"<[^>]+>", " ", text)
    # Unescape common entities
    text = text.replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", "\"")
    # Collapse whitespaces
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_html_title(html: str, fallback_url: str) -> str:
    """Extract <title> from HTML or return fallback."""
    match = re.search(r"<title[^>]*>(.*?)</title>", html, flags=re.DOTALL | re.IGNORECASE)
    if match:
        t = match.group(1).strip()
        t = re.sub(r"\s+", " ", t)
        if t:
            return t
    domain = extract_domain(fallback_url)
    return f"Source from {domain}"


class DirectUrlSourceProvider:
    """Fetches and extracts content directly from explicit user-provided URLs."""

    def __init__(self, user_agent: str = "AISimplifiedLabBot/2.0") -> None:
        self.user_agent = user_agent

    def is_available(self) -> bool:
        return True

    def fetch(self, url: str, timeout: int = 15) -> str:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": self.user_agent,
                "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8",
            },
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            content_type = resp.headers.get("Content-Type", "")
            encoding = "utf-8"
            if "charset=" in content_type:
                encoding = content_type.split("charset=")[-1].split(";")[0].strip()
            raw = resp.read()
            try:
                return raw.decode(encoding)
            except Exception:
                return raw.decode("utf-8", errors="replace")

    def extract_content(self, url: str, timeout: int = 15) -> SourceRecord | None:
        try:
            html = self.fetch(url, timeout=timeout)
            title = extract_html_title(html, url)
            text = clean_html_to_text(html)
            domain = extract_domain(url)
            src_id = f"src_{hashlib.sha256(url.encode()).hexdigest()[:6]}"
            
            # Identify source type
            source_type = "web_article"
            if any(p in domain for p in ("openai.com", "anthropic.com", "deepmind.google", "apple.com", "microsoft.com")):
                source_type = "official_announcement"
            elif any(p in domain for p in ("docs.", "github.com", "arxiv.org")):
                source_type = "documentation"
            elif any(p in domain for p in ("reuters.com", "bloomberg.com", "theverge.com", "wired.com", "techcrunch.com")):
                source_type = "reputable_publication"

            excerpt = text[:1500] if len(text) > 1500 else text

            return SourceRecord(
                source_id=src_id,
                title=title,
                url=url,
                domain=domain,
                source_type=source_type,
                content_excerpt=excerpt,
                summary=excerpt[:300],
                relevance_score=0.8,
            )
        except Exception:
            return None

    def search(self, query: str, limit: int = 5) -> list[SourceRecord]:
        # Direct URL provider doesn't do general search
        return []


class ConfiguredSearchProvider:
    """Configurable web search provider supporting Tavily, Serper, or Brave API keys."""

    def __init__(self) -> None:
        self.tavily_key = os.getenv("TAVILY_API_KEY", "").strip()
        self.serper_key = os.getenv("SERPER_API_KEY", "").strip()
        self.brave_key = os.getenv("BRAVE_API_KEY", "").strip()

    def is_available(self) -> bool:
        return bool(self.tavily_key or self.serper_key or self.brave_key)

    def active_engine(self) -> str:
        if self.tavily_key:
            return "tavily"
        if self.serper_key:
            return "serper"
        if self.brave_key:
            return "brave"
        return "none"

    def search(self, query: str, limit: int = 5) -> list[SourceRecord]:
        if not self.is_available():
            return []

        if self.tavily_key:
            return self._search_tavily(query, limit)
        if self.serper_key:
            return self._search_serper(query, limit)
        if self.brave_key:
            return self._search_brave(query, limit)

        return []

    def _search_tavily(self, query: str, limit: int) -> list[SourceRecord]:
        url = "https://api.tavily.com/search"
        payload = json.dumps({
            "api_key": self.tavily_key,
            "query": query,
            "search_depth": "advanced",
            "max_results": limit,
            "include_raw_content": False,
        }).encode("utf-8")
        req = urllib.request.Request(
            url, payload, headers={"Content-Type": "application/json"}, method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.load(resp)
            records = []
            for idx, item in enumerate(data.get("results", [])):
                src_url = item.get("url", "")
                if not src_url:
                    continue
                domain = extract_domain(src_url)
                src_id = f"src_{idx+1:03d}"
                raw_excerpt = item.get("content", "") or item.get("snippet", "")
                records.append(
                    SourceRecord(
                        source_id=src_id,
                        title=item.get("title", f"Source {idx+1}"),
                        url=src_url,
                        domain=domain,
                        published_at=item.get("published_date"),
                        source_type="web_article",
                        content_excerpt=raw_excerpt[:1500],
                        summary=raw_excerpt[:300],
                        relevance_score=float(item.get("score", 0.8)),
                    )
                )
            return records
        except Exception:
            return []

    def _search_serper(self, query: str, limit: int) -> list[SourceRecord]:
        url = "https://google.serper.dev/search"
        payload = json.dumps({"q": query, "num": limit}).encode("utf-8")
        req = urllib.request.Request(
            url,
            payload,
            headers={"X-API-KEY": self.serper_key, "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.load(resp)
            records = []
            for idx, item in enumerate(data.get("organic", [])[:limit]):
                src_url = item.get("link", "")
                if not src_url:
                    continue
                domain = extract_domain(src_url)
                src_id = f"src_{idx+1:03d}"
                raw_excerpt = item.get("snippet", "")
                records.append(
                    SourceRecord(
                        source_id=src_id,
                        title=item.get("title", f"Source {idx+1}"),
                        url=src_url,
                        domain=domain,
                        published_at=item.get("date"),
                        source_type="web_article",
                        content_excerpt=raw_excerpt[:1500],
                        summary=raw_excerpt[:300],
                        relevance_score=0.75,
                    )
                )
            return records
        except Exception:
            return []

    def _search_brave(self, query: str, limit: int) -> list[SourceRecord]:
        params = urllib.parse.urlencode({"q": query, "count": limit})
        url = f"https://api.search.brave.com/res/v1/web/search?{params}"
        req = urllib.request.Request(
            url,
            headers={"X-Subscription-Token": self.brave_key, "Accept": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.load(resp)
            records = []
            for idx, item in enumerate(data.get("web", {}).get("results", [])[:limit]):
                src_url = item.get("url", "")
                if not src_url:
                    continue
                domain = extract_domain(src_url)
                src_id = f"src_{idx+1:03d}"
                raw_excerpt = item.get("description", "")
                records.append(
                    SourceRecord(
                        source_id=src_id,
                        title=item.get("title", f"Source {idx+1}"),
                        url=src_url,
                        domain=domain,
                        published_at=item.get("page_age"),
                        source_type="web_article",
                        content_excerpt=raw_excerpt[:1500],
                        summary=raw_excerpt[:300],
                        relevance_score=0.75,
                    )
                )
            return records
        except Exception:
            return []

    def fetch(self, url: str, timeout: int = 15) -> str:
        return DirectUrlSourceProvider().fetch(url, timeout=timeout)

    def extract_content(self, url: str, timeout: int = 15) -> SourceRecord | None:
        return DirectUrlSourceProvider().extract_content(url, timeout=timeout)


class MockSourceProvider:
    """Deterministic mock provider for unit testing without network calls."""

    def __init__(self, sources: list[SourceRecord] | None = None) -> None:
        self.sources = sources or []
        self.available = True

    def is_available(self) -> bool:
        return self.available

    def search(self, query: str, limit: int = 5) -> list[SourceRecord]:
        return self.sources[:limit]

    def fetch(self, url: str, timeout: int = 15) -> str:
        for s in self.sources:
            if s.url == url:
                return s.content_excerpt
        return f"<html><title>Mock Page</title><body>Content for {url}</body></html>"

    def extract_content(self, url: str, timeout: int = 15) -> SourceRecord | None:
        for s in self.sources:
            if s.url == url:
                return s
        domain = extract_domain(url)
        return SourceRecord(
            source_id=f"src_{hashlib.sha256(url.encode()).hexdigest()[:6]}",
            title=f"Mock for {domain}",
            url=url,
            domain=domain,
            content_excerpt=f"Extracted content from {url}",
            relevance_score=0.8,
        )
