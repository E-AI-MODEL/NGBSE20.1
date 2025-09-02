"""
Collector manager for NGBSE 20.2.
Manages collector lifecycle and credential validation.
"""
from typing import Any, Dict, List, Type

from ..collectors.base import BaseCollector
from ..collectors.http_web import HttpWebCollector
from ..collectors.leakix import LeakIXCollector
from ..collectors.shodan import ShodanCollector
from ..collectors.censys import CensysCollector
from ..collectors.urlscan import URLScanCollector
from ..collectors.github import GitHubCollector
from ..collectors.news import NewsCollector
from ..logging import get_logger

LOGGER = get_logger(__name__)


class CollectorManager:
    """Manages collector instances and credential validation."""

    # Registry of available collectors
    COLLECTOR_REGISTRY: Dict[str, Type[BaseCollector]] = {
        "http_web": HttpWebCollector,
        "leakix": LeakIXCollector,
        "shodan": ShodanCollector,
        "censys": CensysCollector,
        "urlscan": URLScanCollector,
        "github": GitHubCollector,
        "news": NewsCollector,
    }

    def __init__(self, config: Dict[str, Any], credentials: Dict[str, str]):
        self.config = config
        self.credentials = credentials
        self._collectors: List[BaseCollector] = []

    def build_collectors(self, allowlist: List[str]) -> List[BaseCollector]:
        """Build and validate collector instances."""
        enabled_collectors = self.config.get("collectors", {}).get(
            "enabled", list(self.COLLECTOR_REGISTRY.keys())
        )
        active_collectors = []

        for collector_name in enabled_collectors:
            if collector_name not in self.COLLECTOR_REGISTRY:
                LOGGER.warning(f"Unknown collector: {collector_name}")
                continue

            collector_class = self.COLLECTOR_REGISTRY[collector_name]

            try:
                # Create collector instance
                if collector_name == "http_web":
                    collector = collector_class(allowlist_domains=allowlist)
                else:
                    collector = collector_class(self.config, allowlist)

                # Validate credentials
                if self._has_valid_credentials(collector):
                    active_collectors.append(collector)
                    LOGGER.info(f"Activated collector: {collector_name}")
                else:
                    LOGGER.warning(
                        f"Collector {collector_name} disabled - missing credentials"
                    )

            except Exception as e:
                LOGGER.error(f"Failed to initialize collector {collector_name}: {e}")

        self._collectors = active_collectors
        LOGGER.info(
            f"Active collectors: {[c.__class__.__name__ for c in active_collectors]}"
        )
        return active_collectors

    def _has_valid_credentials(self, collector: BaseCollector) -> bool:
        """Check if collector has valid credentials."""
        if hasattr(collector, 'api_key') and collector.api_key:
            return True
        if hasattr(collector, 'token') and collector.token:
            return True
        if hasattr(collector, 'api_id') and collector.api_id:
            return True
        if isinstance(collector, HttpWebCollector):
            return True
        return False

    def collect_all(
        self, seeds: List[Dict[str, Any]], timestamp: str
    ) -> List[Dict[str, Any]]:
        """Run collection across all active collectors."""
        findings = []

        for seed in seeds:
            seed_findings = []

            for collector in self._collectors:
                try:
                    collector_findings = collector.collect(seed, timestamp)
                    seed_findings.extend(collector_findings)
                    LOGGER.debug(
                        f"Collector {collector.__class__.__name__} found "
                        f"{len(collector_findings)} items for seed {seed.get('id')}"
                    )
                except Exception as e:
                    LOGGER.error(
                        f"Collector {collector.__class__.__name__} failed for "
                        f"seed {seed.get('id')}: {e}"
                    )

            findings.extend(seed_findings)

        return findings
