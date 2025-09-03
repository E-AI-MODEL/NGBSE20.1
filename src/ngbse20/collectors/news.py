"""News collector for recent developments and threat intelligence."""

import os
import requests
from typing import List, Dict, Any
from .base import BaseCollector
from ..utils.hash import content_hash
from ..utils.security import mask_api_key, sanitize_error_message
from ..utils.rate_limiter import retry_with_backoff, api_rate_limited
from ..logging import get_logger

LOGGER = get_logger(__name__)


class NewsCollector(BaseCollector):
    """Collector for news and recent developments."""

    def __init__(self, config: Dict[str, Any], allowlist_domains: List[str]):
        super().__init__(config, allowlist_domains)
        self.api_key = os.getenv("NEWS_API_KEY")
        if not self.api_key:
            LOGGER.warning("News collector requires NEWS_API_KEY env var.")
        else:
            LOGGER.debug(
                f"News collector initialized with API key: {mask_api_key(self.api_key)}"
            )

    def collect(self, seed: Dict[str, Any], now_iso: str) -> List[Dict[str, Any]]:
        """Collect news and recent developments."""
        query = seed.get("query", "")
        if "news" not in (seed.get("type", "").lower() or query.lower()):
            return []

        if not self.api_key:
            return []

        try:
            # Try multiple news APIs for redundancy
            findings = []

            # NewsAPI.org
            try:
                newsapi_findings = self._collect_from_newsapi(query)
                findings.extend(newsapi_findings)
            except Exception as e:
                LOGGER.warning(f"NewsAPI failed: {e}")

            # GNews (backup)
            try:
                gnews_findings = self._collect_from_gnews(query)
                findings.extend(gnews_findings)
            except Exception as e:
                LOGGER.warning(f"GNews failed: {e}")

        except Exception as e:
            sanitized_error = sanitize_error_message(str(e), {"api_key": self.api_key})
            LOGGER.error(
                f"News collector failed for query '{query}': {sanitized_error}"
            )
            return []

        return findings

    @retry_with_backoff(max_retries=3, base_delay=1.0)
    @api_rate_limited("news")
    def _collect_from_newsapi(self, query: str) -> List[Dict[str, Any]]:
        """Collect from NewsAPI.org."""
        url = "https://newsapi.org/v2/everything"
        params = {
            "q": query,
            "apiKey": self.api_key,
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": 50,
        }

        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        findings = []
        for article in data.get("articles", []):
            source_name = article.get("source", {}).get("name", "")
            if not self._is_allowed(source_name):
                continue

            findings.append(
                {
                    "id": f"newsapi-{article.get('url', '').split('/')[-1][:20]}",
                    "hash": content_hash(
                        f"{article.get('title', '')}{article.get('description', '')}"
                    ),
                    "asset": source_name.lower(),
                    "raw": {
                        "title": article.get("title", ""),
                        "description": article.get("description", ""),
                        "author": article.get("author", ""),
                        "url": article.get("url", ""),
                        "published_at": article.get("publishedAt", ""),
                    },
                    "source": {
                        "type": "news",
                        "url": article.get("url", ""),
                        "domain": source_name,
                    },
                    "timestamp": article.get("publishedAt", ""),
                    "quality": {"q": 0.8 if article.get("description") else 0.6},
                }
            )

        return findings

    @retry_with_backoff(max_retries=3, base_delay=1.0)
    @api_rate_limited("news")
    def _collect_from_gnews(self, query: str) -> List[Dict[str, Any]]:
        """Collect from GNews (backup)."""
        url = "https://gnews.io/api/v4/search"
        params = {"q": query, "token": self.api_key, "lang": "en", "max": 50}

        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        findings = []
        for article in data.get("articles", []):
            source_name = article.get("source", {}).get("name", "")
            if not self._is_allowed(source_name):
                continue

            findings.append(
                {
                    "id": f"gnews-{article.get('url', '').split('/')[-1][:20]}",
                    "hash": content_hash(
                        f"{article.get('title', '')}{article.get('description', '')}"
                    ),
                    "asset": source_name.lower(),
                    "raw": {
                        "title": article.get("title", ""),
                        "description": article.get("description", ""),
                        "content": article.get("content", ""),
                        "url": article.get("url", ""),
                        "published_at": article.get("publishedAt", ""),
                    },
                    "source": {
                        "type": "news",
                        "url": article.get("url", ""),
                        "domain": source_name,
                    },
                    "timestamp": article.get("publishedAt", ""),
                    "quality": {"q": 0.8 if article.get("description") else 0.6},
                }
            )

        return findings
