"""Official sources provider for Tier-1 corporate and research blogs.

Fetches announcements and articles directly from official organizations:
- OpenAI (openai.com)
- Anthropic (anthropic.com)
- Google DeepMind / Google AI (deepmind.google, blog.google)
- Meta AI (ai.meta.com)
- NVIDIA (blogs.nvidia.com)
- Microsoft AI (microsoft.com)

All results are classified as source_type="official" and assigned Tier 1.
"""
from __future__ import annotations

import email.utils
import html
import re
from typing import Optional
from urllib.parse import quote_plus
import xml.etree.ElementTree as ET

try:
    import requests
    _REQUESTS_AVAILABLE = True
except ImportError:
    _REQUESTS_AVAILABLE = False

from .base import RawSearchResult, SearchProvider


OFFICIAL_DOMAINS = [
    "openai.com",
    "anthropic.com",
    "deepmind.google",
    "blog.google",
    "ai.meta.com",
    "blogs.nvidia.com",
    "microsoft.com/en-us/research",
]


class OfficialSourcesProvider(SearchProvider):
    """Searches official announcements and lab blogs."""

    @property
    def name(self) -> str:
        return "official"

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

        # Target official domains using site: operator in Google News RSS
        site_filter = " OR ".join(f"site:{d}" for d in OFFICIAL_DOMAINS)
        scoped_query = f"({site_filter}) {query.strip()}"
        if freshness in {"1d", "7d", "30d", "1y"}:
            scoped_query = f"{scoped_query} when:{freshness}"

        url = f"https://news.google.com/rss/search?q={quote_plus(scoped_query)}&hl=en-US&gl=US&ceid=US:en"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        }

        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code != 200:
                return []
            return self._parse_rss(resp.content, query=query, max_results=max_results)
        except Exception:
            return []

    def _parse_rss(self, xml_bytes: bytes, query: str, max_results: int) -> list[RawSearchResult]:
        results: list[RawSearchResult] = []
        try:
            root = ET.fromstring(xml_bytes)
        except Exception:
            return []

        channel = root.find("channel")
        if channel is None:
            return []

        for item in channel.findall("item"):
            title_elem = item.find("title")
            link_elem = item.find("link")
            pub_elem = item.find("pubDate")
            desc_elem = item.find("description")
            source_elem = item.find("source")

            raw_title = title_elem.text if title_elem is not None and title_elem.text else ""
            raw_title = html.unescape(raw_title).strip()
            link = link_elem.text.strip() if link_elem is not None and link_elem.text else ""

            if not raw_title or not link:
                continue

            publisher = "Official Source"
            if source_elem is not None and source_elem.text:
                publisher = source_elem.text.strip()
            if " - " in raw_title:
                parts = raw_title.rsplit(" - ", 1)
                raw_title = parts[0].strip()
                if publisher == "Official Source":
                    publisher = parts[1].strip()

            published_at = None
            if pub_elem is not None and pub_elem.text:
                try:
                    dt = email.utils.parsedate_to_datetime(pub_elem.text)
                    published_at = dt.isoformat()
                except Exception:
                    pass

            snippet = ""
            if desc_elem is not None and desc_elem.text:
                clean_desc = re.sub(r"<[^>]+>", " ", desc_elem.text)
                snippet = html.unescape(clean_desc).strip()
                snippet = re.sub(r"\s+", " ", snippet)

            results.append(RawSearchResult(
                url=link,
                title=raw_title,
                snippet=snippet[:400],
                publisher=publisher,
                published_at=published_at,
                query=query,
                provider=self.name,
                source_type="official",
            ))

            if len(results) >= max_results:
                break

        return results
