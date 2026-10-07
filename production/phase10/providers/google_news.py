"""Google News RSS search provider.

Fetches breaking and recent news articles via public RSS feeds without requiring API keys.
Extracts canonical headlines, publication dates, publishers, and links.
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

from .base import RawSearchResult, SearchProvider, SearchProviderError


class GoogleNewsRSSProvider(SearchProvider):
    """Fetches real-time news articles via Google News RSS."""

    @property
    def name(self) -> str:
        return "google_news"

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

        # Enhance query with freshness constraint for Google News
        q = query.strip()
        if freshness in {"1d", "7d", "30d", "1y"}:
            q = f"{q} when:{freshness}"

        url = f"https://news.google.com/rss/search?q={quote_plus(q)}&hl=en-US&gl=US&ceid=US:en"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        }

        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code != 200:
                return []
            return self._parse_rss(resp.content, query=query, max_results=max_results)
        except Exception:
            # Network issues should not crash the pipeline, return empty
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

            # Split title and publisher if formatted as "Headline - Source Name"
            publisher = ""
            if source_elem is not None and source_elem.text:
                publisher = source_elem.text.strip()
            if " - " in raw_title:
                parts = raw_title.rsplit(" - ", 1)
                raw_title = parts[0].strip()
                if not publisher:
                    publisher = parts[1].strip()

            # Parse date to ISO-8601
            published_at = None
            if pub_elem is not None and pub_elem.text:
                try:
                    dt = email.utils.parsedate_to_datetime(pub_elem.text)
                    published_at = dt.isoformat()
                except Exception:
                    pass

            # Extract text snippet from description (strip html tags)
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
                source_type="news",
            ))

            if len(results) >= max_results:
                break

        return results
