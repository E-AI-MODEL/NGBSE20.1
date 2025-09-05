"""
Collector registry for NGBSE 20.3.
Provides dynamic collector registration and management.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Type, Optional

from ..collectors.base import BaseCollector
from ..logging import get_logger

LOGGER = get_logger(__name__)


class CollectorRegistry(ABC):
    """Abstract base class for collector registries."""
    
    @abstractmethod
    def register_collector(self, name: str, collector_class: Type[BaseCollector]) -> None:
        """Register a collector class."""
        pass
    
    @abstractmethod
    def get_collector(self, name: str) -> Optional[Type[BaseCollector]]:
        """Get a collector class by name."""
        pass
    
    @abstractmethod
    def list_collectors(self) -> List[str]:
        """List all registered collector names."""
        pass
    
    @abstractmethod
    def unregister_collector(self, name: str) -> bool:
        """Unregister a collector class."""
        pass


class DynamicCollectorRegistry(CollectorRegistry):
    """Dynamic collector registry implementation."""
    
    def __init__(self):
        self._collectors: Dict[str, Type[BaseCollector]] = {}
        self._load_builtin_collectors()
    
    def register_collector(self, name: str, collector_class: Type[BaseCollector]) -> None:
        """Register a collector class."""
        if not issubclass(collector_class, BaseCollector):
            raise ValueError(f"Collector class must inherit from BaseCollector")
        
        self._collectors[name] = collector_class
        LOGGER.info(f"Registered collector: {name}")
    
    def get_collector(self, name: str) -> Optional[Type[BaseCollector]]:
        """Get a collector class by name."""
        return self._collectors.get(name)
    
    def list_collectors(self) -> List[str]:
        """List all registered collector names."""
        return list(self._collectors.keys())
    
    def unregister_collector(self, name: str) -> bool:
        """Unregister a collector class."""
        if name in self._collectors:
            del self._collectors[name]
            LOGGER.info(f"Unregistered collector: {name}")
            return True
        return False
    
    def _load_builtin_collectors(self) -> None:
        """Load built-in collectors."""
        try:
            from ..collectors.censys import CensysCollector
            from ..collectors.github import GitHubCollector
            from ..collectors.http_web import HttpWebCollector
            from ..collectors.leakix import LeakIXCollector
            from ..collectors.news import NewsCollector
            from ..collectors.shodan import ShodanCollector
            from ..collectors.urlscan import URLScanCollector
            
            # Register built-in collectors
            self.register_collector("http_web", HttpWebCollector)
            self.register_collector("leakix", LeakIXCollector)
            self.register_collector("shodan", ShodanCollector)
            self.register_collector("censys", CensysCollector)
            self.register_collector("urlscan", URLScanCollector)
            self.register_collector("github", GitHubCollector)
            self.register_collector("news", NewsCollector)
            
            LOGGER.info(f"Loaded {len(self._collectors)} built-in collectors")
            
        except ImportError as e:
            LOGGER.warning(f"Failed to load some built-in collectors: {e}")
    
    def load_external_collector(self, module_path: str, class_name: str, collector_name: str) -> bool:
        """Load an external collector from a module."""
        try:
            import importlib.util
            import sys
            
            spec = importlib.util.spec_from_file_location(collector_name, module_path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[collector_name] = module
            spec.loader.exec_module(module)
            
            collector_class = getattr(module, class_name)
            self.register_collector(collector_name, collector_class)
            return True
            
        except Exception as e:
            LOGGER.error(f"Failed to load external collector {collector_name}: {e}")
            return False