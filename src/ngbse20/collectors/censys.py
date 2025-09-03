"""Censys collector for network and SSL intelligence."""

import os
from typing import Any, Dict, List

import requests

from ..logging import get_logger
from ..utils.hash import content_hash
from ..utils.rate_limiter import api_rate_limited, retry_with_backoff
from ..utils.security import mask_api_key, sanitize_error_message
from .base import BaseCollector

LOGGER = get_logger(__name__)


class CensysCollector(BaseCollector):
    """Collector for Censys network and SSL intelligence."""

    API_BASE = "https://search.censys.io/api/v2"

    def __init__(self, config: Dict[str, Any], allowlist_domains: List[str]):
        super().__init__(config, allowlist_domains)
        self.api_id = os.getenv("CENSYS_API_ID")
        self.api_secret = os.getenv("CENSYS_API_SECRET")
        if not (self.api_id and self.api_secret):
            LOGGER.warning(
                "Censys collector requires CENSYS_API_ID and CENSYS_API_SECRET "
                "env vars."
            )
        else:
            LOGGER.debug(
                f"Censys collector initialized with API ID: "
                f"{mask_api_key(self.api_id)}"
            )

    def collect(self, seed: Dict[str, Any], now_iso: str) -> List[Dict[str, Any]]:
        """Collect network and SSL intelligence from Censys."""
        query = seed.get("query", "")
        if "censys" not in (seed.get("type", "").lower() or query.lower()):
            return []

        if not (self.api_id and self.api_secret):
            return []

        try:
            response = self._make_api_request(query)
            data = response.json()

        except Exception as e:
            sanitized_error = sanitize_error_message(
                str(e), {"api_id": self.api_id, "api_secret": self.api_secret}
            )
            LOGGER.error(
                f"Censys collector failed for query '{query}': {sanitized_error}"
            )
            return []

        findings = []
        for item in data.get("result", {}).get("hits", []):
            ip = item.get("ip", "")
            domain = item.get("names", [""])[0] if item.get("names") else ""

            # Check if domain is allowed
            if domain and not self._is_allowed(domain):
                continue

            # For IP-based findings, check if any hostname is allowed
            if not domain and item.get("names"):
                allowed_hostname = None
                for hostname in item.get("names", []):
                    if self._is_allowed(hostname):
                        allowed_hostname = hostname
                        break
                if not allowed_hostname:
                    continue
                domain = allowed_hostname

            # Extract SSL certificate info
            ssl_info = {}
            if "services" in item:
                for service in item["services"]:
                    if "tls" in service:
                        ssl_info = {
                            "certificate": service["tls"]
                            .get("certificates", {})
                            .get("leaf_data", {}),
                            "version": service["tls"].get("version", ""),
                            "cipher_suite": service["tls"].get("cipher_suite", {}),
                        }
                        break

            findings.append(
                {
                    "id": (
                        f"censys-{ip}-"
                        f"{item.get('location', {}).get('country', 'unknown')}"
                    ),
                    "hash": content_hash(f"{ip}{domain}{str(ssl_info)}"),
                    "asset": domain.lower() if domain else ip,
                    "raw": {
                        "ip": ip,
                        "location": item.get("location", {}),
                        "ssl_info": ssl_info,
                        "ports": [s.get("port") for s in item.get("services", [])],
                        "protocols": [
                            s.get("transport_protocol")
                            for s in item.get("services", [])
                        ],
                    },
                    "source": {
                        "type": "network_intelligence",
                        "url": f"https://censys.io/ipv4/{ip}",
                        "domain": domain or ip,
                    },
                    "timestamp": item.get("last_updated", now_iso),
                    "quality": {"q": 0.8 if ssl_info else 0.6},
                }
            )

        return findings

    @retry_with_backoff(max_retries=3, base_delay=1.0)
    @api_rate_limited("censys")
    def _make_api_request(self, query: str):
        """Make rate-limited API request to Censys."""
        params = {"q": query, "per_page": 100}

        response = requests.get(
            f"{self.API_BASE}/hosts/search",
            params=params,
            auth=(self.api_id, self.api_secret),
            timeout=30,
        )
        response.raise_for_status()
        return response
