"""Source fetcher: retrieves page titles and metadata from candidate URLs.

This module does real HTTP fetches to validate that URLs exist and
extract structured metadata. It NEVER generates URLs via LLM.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import urlparse

try:
    import requests
    _REQUESTS_AVAILABLE = True
except ImportError:
    _REQUESTS_AVAILABLE = False

# Domain → tier mapping
_TIER1_DOMAINS = {
    "openai.com", "anthropic.com", "deepmind.google", "ai.google",
    "blog.google", "research.google", "ai.meta.com", "llama.meta.com",
    "microsoft.com", "nvidia.com", "huggingface.co", "github.com",
    "arxiv.org",
}
_TIER2_DOMAINS = {
    "reuters.com", "apnews.com", "bloomberg.com", "ft.com",
    "wsj.com", "nytimes.com", "bbc.com",
}
_TIER3_DOMAINS = {
    "techcrunch.com", "theverge.com", "arstechnica.com", "venturebeat.com",
    "wired.com", "zdnet.com", "engadget.com", "9to5google.com",
}
_TIER4_DOMAINS = {"twitter.com", "x.com", "reddit.com", "threads.net"}


def infer_tier(url: str) -> int:
    try:
        host = urlparse(url).hostname or ""
        host = host.removeprefix("www.")
        if any(host == d or host.endswith("." + d) for d in _TIER1_DOMAINS):
            return 1
        if any(host == d or host.endswith("." + d) for d in _TIER2_DOMAINS):
            return 2
        if any(host == d or host.endswith("." + d) for d in _TIER3_DOMAINS):
            return 3
        if any(host == d or host.endswith("." + d) for d in _TIER4_DOMAINS):
            return 4
        return 3
    except Exception:
        return 3


def fetch_title(url: str, timeout: int = 8) -> Optional[str]:
    """Fetch a URL and extract its <title> tag. Returns None on failure."""
    if not _REQUESTS_AVAILABLE:
        return None
    try:
        resp = requests.get(
            url,
            timeout=timeout,
            headers={"User-Agent": "AI-Simplified-Research-Bot/1.0 (+https://github.com)"},
            allow_redirects=True,
        )
        if resp.status_code >= 400:
            return None
        html = resp.text[:8000]
        m = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
        if m:
            return re.sub(r"\s+", " ", m.group(1)).strip()
        return None
    except Exception:
        return None


def validate_url(url: str) -> bool:
    """Return True if the URL is well-formed and resolvable (HEAD check)."""
    if not _REQUESTS_AVAILABLE:
        return False
    try:
        parsed = urlparse(url)
        if not (parsed.scheme and parsed.hostname):
            return False
        resp = requests.head(url, timeout=8, allow_redirects=True,
                             headers={"User-Agent": "AI-Simplified-Research-Bot/1.0"})
        return resp.status_code < 400
    except Exception:
        return False
