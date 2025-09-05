"""
Unit tests for NGBSE 20.3 collector system.
Tests collector registry and manager functionality.
"""

from unittest.mock import Mock, patch
import pytest

from ngbse20.runtime.collector_registry import DynamicCollectorRegistry, CollectorRegistry
from ngbse20.runtime.collector_manager import CollectorManager


class TestCollectorRegistry:
    """Test collector registry functionality."""
    
    def test_collector_registry_interface(self):
        """Test collector registry interface."""
        # Mock collector class
        class MockCollector:
            def __init__(self, config, allowlist):
                pass
        
        registry = DynamicCollectorRegistry()
        
        # Test registration
        registry.register_collector("test_collector", MockCollector)
        assert "test_collector" in registry.list_collectors()
        
        # Test retrieval
        collector_class = registry.get_collector("test_collector")
        assert collector_class == MockCollector
        
        # Test unregistration
        result = registry.unregister_collector("test_collector")
        assert result is True
        assert "test_collector" not in registry.list_collectors()
    
    def test_collector_registry_invalid_class(self):
        """Test registry with invalid collector class."""
        registry = DynamicCollectorRegistry()
        
        class InvalidCollector:
            pass  # Not inheriting from BaseCollector
        
        with pytest.raises(ValueError):
            registry.register_collector("invalid", InvalidCollector)
    
    def test_collector_registry_duplicate_registration(self):
        """Test duplicate collector registration."""
        registry = DynamicCollectorRegistry()
        
        class MockCollector:
            def __init__(self, config, allowlist):
                pass
        
        # First registration
        registry.register_collector("test", MockCollector)
        assert "test" in registry.list_collectors()
        
        # Second registration should overwrite
        registry.register_collector("test", MockCollector)
        assert "test" in registry.list_collectors()
    
    def test_collector_registry_nonexistent_collector(self):
        """Test operations on nonexistent collector."""
        registry = DynamicCollectorRegistry()
        
        # Get nonexistent collector
        collector = registry.get_collector("nonexistent")
        assert collector is None
        
        # Unregister nonexistent collector
        result = registry.unregister_collector("nonexistent")
        assert result is False
    
    @patch('ngbse20.runtime.collector_registry.importlib.util')
    def test_load_external_collector_success(self, mock_importlib):
        """Test successful external collector loading."""
        # Mock importlib components
        mock_spec = Mock()
        mock_module = Mock()
        mock_loader = Mock()
        
        mock_importlib.spec_from_file_location.return_value = mock_spec
        mock_importlib.module_from_spec.return_value = mock_module
        mock_spec.loader = mock_loader
        
        # Mock collector class
        class ExternalCollector:
            def __init__(self, config, allowlist):
                pass
        
        mock_module.ExternalCollector = ExternalCollector
        
        registry = DynamicCollectorRegistry()
        result = registry.load_external_collector(
            "/path/to/collector.py", "ExternalCollector", "external"
        )
        
        assert result is True
        assert "external" in registry.list_collectors()
    
    @patch('ngbse20.runtime.collector_registry.importlib.util')
    def test_load_external_collector_failure(self, mock_importlib):
        """Test external collector loading failure."""
        mock_importlib.spec_from_file_location.side_effect = ImportError("Module not found")
        
        registry = DynamicCollectorRegistry()
        result = registry.load_external_collector(
            "/path/to/collector.py", "ExternalCollector", "external"
        )
        
        assert result is False
        assert "external" not in registry.list_collectors()


class TestCollectorManager:
    """Test collector manager functionality."""
    
    def test_collector_manager_initialization(self):
        """Test collector manager initialization."""
        config = {"collectors": {"enabled": ["http_web"]}}
        credentials = {"shodan": "test_key"}
        
        manager = CollectorManager(config, credentials)
        
        assert manager.config == config
        assert manager.credentials == credentials
        assert len(manager._collectors) == 0
    
    def test_has_required_credentials_http_web(self):
        """Test credential check for http_web collector."""
        config = {}
        credentials = {}
        
        manager = CollectorManager(config, credentials)
        
        # HttpWebCollector doesn't need credentials
        assert manager._has_required_credentials("http_web") is True
    
    def test_has_required_credentials_with_credentials(self):
        """Test credential check with available credentials."""
        config = {}
        credentials = {"shodan": "test_key"}
        
        manager = CollectorManager(config, credentials)
        
        assert manager._has_required_credentials("shodan") is True
        assert manager._has_required_credentials("censys") is False
    
    def test_has_required_credentials_patterns(self):
        """Test credential check with different patterns."""
        config = {}
        credentials = {
            "shodan_api_key": "test_key",
            "censys_token": "test_token",
            "leakix_key": "test_key"
        }
        
        manager = CollectorManager(config, credentials)
        
        assert manager._has_required_credentials("shodan") is True
        assert manager._has_required_credentials("censys") is True
        assert manager._has_required_credentials("leakix") is True
        assert manager._has_required_credentials("urlscan") is False
    
    def test_has_valid_credentials_http_web(self):
        """Test credential validation for http_web collector."""
        config = {}
        credentials = {}
        
        manager = CollectorManager(config, credentials)
        
        # Mock HttpWebCollector
        class MockHttpWebCollector:
            pass
        
        collector = MockHttpWebCollector()
        
        # Mock isinstance check
        with patch('ngbse20.runtime.collector_manager.HttpWebCollector', MockHttpWebCollector):
            with patch('isinstance', return_value=True):
                assert manager._has_valid_credentials(collector) is True
    
    def test_has_valid_credentials_with_api_key(self):
        """Test credential validation with API key."""
        config = {}
        credentials = {}
        
        manager = CollectorManager(config, credentials)
        
        # Mock collector with API key
        class MockCollector:
            def __init__(self):
                self.api_key = "test_key"
        
        collector = MockCollector()
        assert manager._has_valid_credentials(collector) is True
    
    def test_has_valid_credentials_with_token(self):
        """Test credential validation with token."""
        config = {}
        credentials = {}
        
        manager = CollectorManager(config, credentials)
        
        # Mock collector with token
        class MockCollector:
            def __init__(self):
                self.token = "test_token"
        
        collector = MockCollector()
        assert manager._has_valid_credentials(collector) is True
    
    def test_has_valid_credentials_with_api_id(self):
        """Test credential validation with API ID."""
        config = {}
        credentials = {}
        
        manager = CollectorManager(config, credentials)
        
        # Mock collector with API ID
        class MockCollector:
            def __init__(self):
                self.api_id = "test_id"
        
        collector = MockCollector()
        assert manager._has_valid_credentials(collector) is True
    
    def test_has_valid_credentials_from_credentials_dict(self):
        """Test credential validation from credentials dictionary."""
        config = {}
        credentials = {"shodan": "test_key"}
        
        manager = CollectorManager(config, credentials)
        
        # Mock collector
        class MockCollector:
            def __init__(self):
                pass
        
        collector = MockCollector()
        
        # Mock collector name
        with patch.object(collector, '__class__', Mock(__name__='ShodanCollector')):
            assert manager._has_valid_credentials(collector) is True
    
    def test_has_valid_credentials_no_credentials(self):
        """Test credential validation without credentials."""
        config = {}
        credentials = {}
        
        manager = CollectorManager(config, credentials)
        
        # Mock collector without credentials
        class MockCollector:
            def __init__(self):
                pass
        
        collector = MockCollector()
        
        # Mock collector name
        with patch.object(collector, '__class__', Mock(__name__='ShodanCollector')):
            assert manager._has_valid_credentials(collector) is False
    
    @patch('ngbse20.runtime.collector_manager.DynamicCollectorRegistry')
    def test_build_collectors_with_credentials(self, mock_registry_class):
        """Test building collectors with valid credentials."""
        # Mock registry
        mock_registry = Mock()
        mock_registry_class.return_value = mock_registry
        
        # Mock collector class
        class MockCollector:
            def __init__(self, config, allowlist):
                self.api_key = "test_key"
        
        mock_registry.list_collectors.return_value = ["shodan"]
        mock_registry.get_collector.return_value = MockCollector
        
        config = {"collectors": {"enabled": ["shodan"]}}
        credentials = {"shodan": "test_key"}
        
        manager = CollectorManager(config, credentials)
        
        # Mock the credential check methods
        manager._has_required_credentials = Mock(return_value=True)
        manager._has_valid_credentials = Mock(return_value=True)
        
        collectors = manager.build_collectors(["*"])
        
        assert len(collectors) == 1
        assert isinstance(collectors[0], MockCollector)
    
    @patch('ngbse20.runtime.collector_manager.DynamicCollectorRegistry')
    def test_build_collectors_missing_credentials(self, mock_registry_class):
        """Test building collectors with missing credentials."""
        # Mock registry
        mock_registry = Mock()
        mock_registry_class.return_value = mock_registry
        
        mock_registry.list_collectors.return_value = ["shodan"]
        mock_registry.get_collector.return_value = Mock()
        
        config = {"collectors": {"enabled": ["shodan"]}}
        credentials = {}
        
        manager = CollectorManager(config, credentials)
        
        # Mock the credential check methods
        manager._has_required_credentials = Mock(return_value=False)
        
        collectors = manager.build_collectors(["*"])
        
        assert len(collectors) == 0
    
    def test_list_available_collectors(self):
        """Test listing available collectors."""
        config = {}
        credentials = {}
        
        manager = CollectorManager(config, credentials)
        
        # Mock registry
        manager.registry.list_collectors = Mock(return_value=["http_web", "shodan"])
        
        collectors = manager.list_available_collectors()
        
        assert "http_web" in collectors
        assert "shodan" in collectors
    
    def test_get_collector_info(self):
        """Test getting collector information."""
        config = {}
        credentials = {}
        
        manager = CollectorManager(config, credentials)
        
        # Mock collector class
        class MockCollector:
            __name__ = "TestCollector"
            __module__ = "test.module"
            __doc__ = "Test collector documentation"
        
        # Mock registry
        manager.registry.get_collector = Mock(return_value=MockCollector)
        
        info = manager.get_collector_info("test")
        
        assert info is not None
        assert info["name"] == "test"
        assert info["class"] == "TestCollector"
        assert info["module"] == "test.module"
        assert info["description"] == "Test collector documentation"
    
    def test_get_collector_info_nonexistent(self):
        """Test getting info for nonexistent collector."""
        config = {}
        credentials = {}
        
        manager = CollectorManager(config, credentials)
        
        # Mock registry
        manager.registry.get_collector = Mock(return_value=None)
        
        info = manager.get_collector_info("nonexistent")
        
        assert info is None
    
    def test_register_collector(self):
        """Test registering a new collector."""
        config = {}
        credentials = {}
        
        manager = CollectorManager(config, credentials)
        
        # Mock collector class
        class MockCollector:
            def __init__(self, config, allowlist):
                pass
        
        # Mock registry
        manager.registry.register_collector = Mock()
        
        result = manager.register_collector("test", MockCollector)
        
        assert result is True
        manager.registry.register_collector.assert_called_once_with("test", MockCollector)
    
    def test_unregister_collector(self):
        """Test unregistering a collector."""
        config = {}
        credentials = {}
        
        manager = CollectorManager(config, credentials)
        
        # Mock registry
        manager.registry.unregister_collector = Mock(return_value=True)
        
        result = manager.unregister_collector("test")
        
        assert result is True
        manager.registry.unregister_collector.assert_called_once_with("test")


if __name__ == "__main__":
    pytest.main([__file__])