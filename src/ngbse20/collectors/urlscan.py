"""URLScan collector for threat intelligence."""

import os
from typing import Any

import requests

from ..logging import get_logger
from ..utils.hash import content_hash
from ..utils.rate_limiter import api_rate_limited, retry_with_backoff
from ..utils.security import mask_api_key, sanitize_error_message
from .base import BaseCollector

LOGGER = get_logger(__name__)


class URLScanCollector(BaseCollector):
    """Collector for URLScan threat intelligence."""

    API_BASE = "https://urlscan.io/api/v1"

    def __init__(self, config: dict[str, Any], allowlist_domains: list[str]):
        super().__init__(config, allowlist_domains)
        self.api_key = os.getenv("URLSCAN_API_KEY")
        if not self.api_key:
            LOGGER.warning("URLScan collector requires URLSCAN_API_KEY env var.")
        else:
            LOGGER.debug(
                f"URLScan collector initialized with API key: {mask_api_key(self.api_key)}"
            )

    def collect(self, seed: dict[str, Any], now_iso: str) -> list[dict[str, Any]]:
        """Collect threat intelligence from URLScan."""
        query = seed.get("query", "")
        if "urlscan" not in (seed.get("type", "").lower() or query.lower()):
            return []

        if not self.api_key:
            return []

        try:
            response = self._make_api_request(query)
            data = response.json()

        except Exception as e:
            sanitized_error = sanitize_error_message(str(e), {"api_key": self.api_key})
            LOGGER.error(
                f"URLScan collector failed for query '{query}': {sanitized_error}"
            )
            return []

        findings = []
        for item in data.get("results", []):
            page = item.get("page", {})
            url = page.get("url", "")
            domain = page.get("domain", "")

            if not self._is_allowed(domain):
                continue

            # Extract threat indicators
            threat_indicators = []
            if "stats" in item:
                stats = item["stats"]
                if stats.get("malicious", 0) > 0:
                    threat_indicators.append("malicious")
                if stats.get("suspicious", 0) > 0:
                    threat_indicators.append("suspicious")

            findings.append(
                {
                    "id": f"urlscan-{item.get('_id', 'unknown')}",
                    "hash": content_hash(
                        f"{url}{page.get('title', '')}{threat_indicators!s}"
                    ),
                    "asset": domain.lower(),
                    "raw": {
                        "url": url,
                        "title": page.get("title", ""),
                        "threat_indicators": threat_indicators,
                        "malicious_score": item.get("stats", {}).get("malicious", 0),
                        "suspicious_score": item.get("stats", {}).get("suspicious", 0),
                        "scan_time": item.get("task", {}).get("time", ""),
                    },
                    "source": {
                        "type": "threat_intelligence",
                        "url": f"https://urlscan.io/result/{item.get('_id', '')}",
                        "domain": domain,
                    },
                    "timestamp": item.get("task", {}).get("time", now_iso),
                    "quality": {"q": 0.9 if threat_indicators else 0.7},
                }
            )

        return findings

    @retry_with_backoff(max_retries=3, base_delay=1.0)
    @api_rate_limited("urlscan")
    def _make_api_request(self, query: str):
        """Make rate-limited API request to URLScan."""
        headers = {"API-Key": self.api_key}
        params = {"q": query, "size": 100}

        response = requests.get(
            f"{self.API_BASE}/search/", headers=headers, params=params, timeout=30
        )
        response.raise_for_status()
        return response
