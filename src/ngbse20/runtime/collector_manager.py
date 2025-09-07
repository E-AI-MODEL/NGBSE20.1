"""
Enhanced collector manager for NGBSE 20.3.
Manages collector lifecycle, credential validation, and dynamic loading.
"""

from typing import Any, Dict, List, Optional

from ..collectors.base import BaseCollector
from ..collectors.http_web import HttpWebCollector
from ..logging import get_logger
from .collector_registry import DynamicCollectorRegistry

LOGGER = get_logger(__name__)


class CollectorManager:
    """Enhanced collector manager with dynamic registry support."""

    def __init__(self, config: Dict[str, Any], credentials: Dict[str, str]):
        self.config = config
        self.credentials = credentials
        self.registry = DynamicCollectorRegistry()
        self._collectors: List[BaseCollector] = []
        
        # Load external collectors if configured
        self._load_external_collectors()

    def build_collectors(self, allowlist: List[str]) -> List[BaseCollector]:
        """Build and validate collector instances using dynamic registry."""
        # Handle both dict and Pydantic model config
        if hasattr(self.config, 'collectors'):
            # Pydantic model
            collectors_config = self.config.collectors
            enabled_collectors = collectors_config.enabled if collectors_config.enabled else self.registry.list_collectors()
        else:
            # Dictionary
            enabled_collectors = self.config.get("collectors", {}).get("enabled", self.registry.list_collectors())
        
        active_collectors = []
        missing_credentials = []

        for collector_name in enabled_collectors:
            collector_class = self.registry.get_collector(collector_name)
            if not collector_class:
                LOGGER.warning(f"Unknown collector: {collector_name}")
                continue

            # Check credentials before creating collector instance
            if not self._has_required_credentials(collector_name):
                missing_credentials.append(collector_name)
                LOGGER.warning(f"Collector {collector_name} disabled - missing API credentials")
                continue

            try:
                # Create collector instance
                # RESTORED: Speciale behandeling voor http_web collector
                if collector_name == "http_web":
                    collector = collector_class(allowlist_domains=allowlist)
                else:
                    collector = collector_class(self.config, allowlist)

                # Additional validation after creation
                if self._has_valid_credentials(collector):
                    active_collectors.append(collector)
                    LOGGER.info(f"Activated collector: {collector_name}")
                else:
                    LOGGER.warning(f"Collector {collector_name} disabled - credential validation failed")

            except Exception as e:
                LOGGER.error(f"Failed to initialize collector {collector_name}: {e}")

        # Log summary
        if missing_credentials:
            LOGGER.info(f"Collectors disabled due to missing credentials: {missing_credentials}")
        
        self._collectors = active_collectors
        LOGGER.info(f"Active collectors: {[c.__class__.__name__ for c in active_collectors]}")
        return active_collectors

    def _has_valid_credentials(self, collector: BaseCollector) -> bool:
        """Check if collector has valid credentials."""
        # HttpWebCollector doesn't need API keys
        if isinstance(collector, HttpWebCollector):
            return True
        
        # Check collector-specific credential attributes
        if hasattr(collector, "api_key") and collector.api_key:
            return True
        if hasattr(collector, "token") and collector.token:
            return True
        if hasattr(collector, "api_id") and collector.api_id:
            return True
        
        # Check if credentials are available in self.credentials
        collector_name = collector.__class__.__name__.lower().replace("collector", "")
        if collector_name in self.credentials and self.credentials[collector_name]:
            return True
        
        # Check for common API key patterns in credentials
        api_key_patterns = [
            f"{collector_name}_api_key",
            f"{collector_name}_token",
            f"{collector_name}_key",
            "api_key",
            "token"
        ]
        
        for pattern in api_key_patterns:
            if pattern in self.credentials and self.credentials[pattern]:
                return True
        
        return False
    
    def _has_required_credentials(self, collector_name: str) -> bool:
        """Check if required credentials are available before creating collector."""
        # HttpWebCollector doesn't need API keys
        if collector_name == "http_web":
            return True
        
        # Check for collector-specific credentials
        if collector_name in self.credentials and self.credentials[collector_name]:
            return True
        
        # Check for common API key patterns
        api_key_patterns = [
            f"{collector_name}_api_key",
            f"{collector_name}_token", 
            f"{collector_name}_key",
            f"{collector_name}_id",
            "api_key",
            "token"
        ]
        
        for pattern in api_key_patterns:
            if pattern in self.credentials and self.credentials[pattern]:
                return True
        
        return False

    def collect_all(self, seeds: list[dict[str, Any]], timestamp: str) -> list[dict[str, Any]]:
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
                    LOGGER.error(f"Collector {collector.__class__.__name__} failed for " f"seed {seed.get('id')}: {e}")

            findings.extend(seed_findings)

        return findings
    
    def _load_external_collectors(self) -> None:
        """Load external collectors from configuration."""
        external_collectors = self.config.get("external_collectors", [])
        
        for collector_config in external_collectors:
            if isinstance(collector_config, dict):
                module_path = collector_config.get("module_path")
                class_name = collector_config.get("class_name")
                collector_name = collector_config.get("name")
                
                if module_path and class_name and collector_name:
                    success = self.registry.load_external_collector(
                        module_path, class_name, collector_name
                    )
                    if success:
                        LOGGER.info(f"Loaded external collector: {collector_name}")
                    else:
                        LOGGER.warning(f"Failed to load external collector: {collector_name}")
    
    def register_collector(self, name: str, collector_class: type[BaseCollector]) -> None:
        """Register a new collector dynamically."""
        self.registry.register_collector(name, collector_class)
    
    def list_available_collectors(self) -> List[str]:
        """List all available collectors."""
        return self.registry.list_collectors()
    
    def get_collector_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific collector."""
        collector_class = self.registry.get_collector(name)
        if collector_class:
            return {
                "name": name,
                "class": collector_class.__name__,
                "module": collector_class.__module__,
                "description": getattr(collector_class, "__doc__", "").strip() if getattr(collector_class, "__doc__", None) else ""
            }
        return None
