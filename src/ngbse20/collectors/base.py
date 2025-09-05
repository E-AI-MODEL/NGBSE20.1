"""Base collector class for NGBSE 20.1."""

from abc import ABC, abstractmethod
from typing import Any

import tldextract


class BaseCollector(ABC):
    """Base class for all NGBSE collectors."""

    def __init__(self, config: dict[str, Any], allowlist_domains: list[str]):
        """Initialize collector with configuration and domain allowlist."""
        self.config = config
        self.allow_domains = [d.lower() for d in allowlist_domains]

    def _is_allowed(self, domain: str) -> bool:
        """Check if domain is in allowlist."""
        if not domain:
            return False

        d = domain.lower()

        # Wildcard allows all domains
        if "*" in self.allow_domains:
            return True

        # Exact match
        if d in self.allow_domains:
            return True

        # Subdomain matching (e.g., .example.com matches sub.example.com)
        return any(entry.startswith(".") and d.endswith(entry) for entry in self.allow_domains)

    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL using tldextract."""
        try:
            ext = tldextract.extract(url)
            if ext.top_domain_under_public_suffix:
                return ext.top_domain_under_public_suffix
            return ".".join(p for p in [ext.domain, ext.suffix] if p)
        except Exception:
            # Fallback to basic URL parsing
            from urllib.parse import urlparse

            parsed = urlparse(url)
            host = parsed.netloc.split("@")[-1].split(":")[0]
            if host.startswith("www."):
                host = host[4:]
            return host

    @abstractmethod
    def collect(self, seed: dict[str, Any], now_iso: str) -> list[dict[str, Any]]:
        """Collect data from the source. Must be implemented by subclasses."""
        raise NotImplementedError

    def get_collector_info(self) -> dict[str, Any]:
        """Get information about this collector."""
        return {
            "name": self.__class__.__name__,
            "description": self.__class__.__doc__ or "No description available",
            "requires_api_key": hasattr(self, "api_key") or hasattr(self, "token") or hasattr(self, "api_id"),
            "active": self._is_active(),
        }

    def _is_active(self) -> bool:
        """Check if collector is active (has required credentials)."""
        if hasattr(self, "api_key") and not self.api_key:
            return False
        if hasattr(self, "token") and not self.token:
            return False
        return not (hasattr(self, "api_id") and not self.api_id)
