"""Shodan collector for IoT and infrastructure intelligence."""

import os
import requests
from typing import List, Dict, Any
from .base import BaseCollector
from ..utils.hash import content_hash
from ..utils.security import mask_api_key, sanitize_error_message
from ..utils.rate_limiter import retry_with_backoff, api_rate_limited
from ..logging import get_logger

LOGGER = get_logger(__name__)


class ShodanCollector(BaseCollector):
    """Collector for Shodan IoT and infrastructure intelligence."""

    API_BASE = "https://api.shodan.io"

    def __init__(self, config: Dict[str, Any], allowlist_domains: List[str]):
        super().__init__(config, allowlist_domains)
        self.api_key = os.getenv("SHODAN_API_KEY")
        if not self.api_key:
            LOGGER.warning("Shodan collector requires SHODAN_API_KEY env var.")
        else:
            LOGGER.debug(f"Shodan collector initialized with API key: {mask_api_key(self.api_key)}")

    def collect(self, seed: Dict[str, Any], now_iso: str) -> List[Dict[str, Any]]:
        """Collect IoT and infrastructure intelligence from Shodan."""
        query = seed.get("query", "")
        if "shodan" not in (seed.get("type", "").lower() or query.lower()):
            return []

        if not self.api_key:
            return []

        try:
            response = self._make_api_request(query)
            data = response.json()

        except Exception as e:
            sanitized_error = sanitize_error_message(str(e), {"api_key": self.api_key})
            LOGGER.error(f"Shodan collector failed for query '{query}': {sanitized_error}")
            return []

        findings = []
        for item in data.get("matches", []):
            ip = item.get("ip_str", "")
            domain = item.get("hostnames", [""])[0] if item.get("hostnames") else ""

            # Check if domain is allowed
            if domain and not self._is_allowed(domain):
                continue

            # For IP-based findings, check if any hostname is allowed
            if not domain and item.get("hostnames"):
                allowed_hostname = None
                for hostname in item.get("hostnames", []):
                    if self._is_allowed(hostname):
                        allowed_hostname = hostname
                        break
                if not allowed_hostname:
                    continue
                domain = allowed_hostname

            findings.append({
                "id": f"shodan-{ip}-{item.get('port', 'unknown')}",
                "hash": content_hash(f"{ip}{item.get('port', '')}{item.get('data', '')}"),
                "asset": domain.lower() if domain else ip,
                "raw": {
                    "ip": ip,
                    "port": item.get("port", ""),
                    "product": item.get("product", ""),
                    "version": item.get("version", ""),
                    "os": item.get("os", ""),
                    "data": item.get("data", "")[:1000]  # Limit data size
                },
                "source": {
                    "type": "infrastructure",
                    "url": f"https://shodan.io/host/{ip}",
                    "domain": domain or ip
                },
                "timestamp": item.get("timestamp", now_iso),
                "quality": {"q": 0.7 if item.get("product") else 0.5}
            })

        return findings

    @retry_with_backoff(max_retries=3, base_delay=1.0)
    @api_rate_limited('shodan')
    def _make_api_request(self, query: str):
        """Make rate-limited API request to Shodan."""
        params = {"key": self.api_key, "query": query, "limit": 100}

        response = requests.get(
            f"{self.API_BASE}/shodan/host/search",
            params=params,
            timeout=30
        )
        response.raise_for_status()
        return response
