"""LeakIX collector for data breach intelligence."""

import os
import requests
from typing import List, Dict, Any
from .base import BaseCollector
from ..utils.hash import content_hash
from ..utils.security import mask_api_key, sanitize_error_message
from ..utils.rate_limiter import retry_with_backoff, api_rate_limited
from ..logging import get_logger

LOGGER = get_logger(__name__)


class LeakIXCollector(BaseCollector):
    """Collector for LeakIX data breach intelligence."""

    API_BASE = "https://leakix.net/api"

    def __init__(self, config: Dict[str, Any], allowlist_domains: List[str]):
        super().__init__(config, allowlist_domains)
        self.api_key = os.getenv("LEAKIX_API_KEY")
        if not self.api_key:
            LOGGER.warning("LeakIX collector requires LEAKIX_API_KEY env var.")
        else:
            LOGGER.debug(
                f"LeakIX collector initialized with API key: "
                f"{mask_api_key(self.api_key)}"
            )

    def collect(self, seed: Dict[str, Any], now_iso: str) -> List[Dict[str, Any]]:
        """Collect data breach intelligence from LeakIX."""
        query = seed.get("query", "")
        if "leakix" not in (seed.get("type", "").lower() or query.lower()):
            return []

        if not self.api_key:
            return []

        try:
            response = self._make_api_request(query)
            data = response.json()

        except Exception as e:
            sanitized_error = sanitize_error_message(str(e), {"api_key": self.api_key})
            LOGGER.error(
                f"LeakIX collector failed for query '{query}': {sanitized_error}"
            )
            return []

        findings = []
        for item in data.get("results", []):
            domain = item.get("domain", "")
            if not self._is_allowed(domain):
                continue

            findings.append(
                {
                    "id": f"leakix-{item.get('id', 'unknown')}",
                    "hash": content_hash(
                        f"{domain}{item.get('title', '')}{item.get('content', '')}"
                    ),
                    "asset": domain.lower(),
                    "raw": {
                        "title": item.get("title", ""),
                        "content": item.get("content", ""),
                        "type": item.get("type", ""),
                        "severity": item.get("severity", "medium"),
                    },
                    "source": {
                        "type": "data_breach",
                        "url": f"https://leakix.net/breach/{item.get('id', '')}",
                        "domain": domain,
                    },
                    "timestamp": item.get("discovered_at", now_iso),
                    "quality": {"q": 0.8 if item.get("verified") else 0.5},
                }
            )

        return findings

    @retry_with_backoff(max_retries=3, base_delay=1.0)
    @api_rate_limited("leakix")
    def _make_api_request(self, query: str):
        """Make rate-limited API request to LeakIX."""
        headers = {"Authorization": f"Bearer {self.api_key}"}
        params = {"q": query, "size": 50}

        response = requests.get(
            f"{self.API_BASE}/search", headers=headers, params=params, timeout=30
        )
        response.raise_for_status()
        return response
