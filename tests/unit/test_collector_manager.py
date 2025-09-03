"""
Unit tests for CollectorManager.
"""

from unittest.mock import Mock, patch

from src.ngbse20.runtime.collector_manager import CollectorManager


class TestCollectorManager:
    """Test cases for CollectorManager."""

    def test_collector_registry(self):
        """Test collector registry contains expected collectors."""
        manager = CollectorManager({}, {})

        expected_collectors = [
            "http_web",
            "leakix",
            "shodan",
            "censys",
            "urlscan",
            "github",
            "news",
        ]

        for collector_name in expected_collectors:
            assert collector_name in manager.COLLECTOR_REGISTRY

    def test_build_collectors_with_credentials(self):
        """Test building collectors with valid credentials."""
        config = {"collectors": {"enabled": ["http_web", "shodan"]}}
        credentials = {"SHODAN_API_KEY": "test_key"}

        with patch("src.ngbse20.runtime.collector_manager.ShodanCollector") as mock_shodan:
            mock_instance = Mock()
            mock_instance.api_key = "test_key"
            mock_shodan.return_value = mock_instance

            with patch("src.ngbse20.runtime.collector_manager.HttpWebCollector") as mock_http:
                mock_http_instance = Mock()
                mock_http.return_value = mock_http_instance

                manager = CollectorManager(config, credentials)
                collectors = manager.build_collectors(["*"])

                # HttpWebCollector should always be included
                assert len(collectors) >= 1

    def test_build_collectors_without_credentials(self):
        """Test building collectors without credentials."""
        config = {"collectors": {"enabled": ["shodan", "censys"]}}
        credentials = {}  # No credentials

        manager = CollectorManager(config, credentials)
        collectors = manager.build_collectors(["*"])

        # Should only include collectors that don't need credentials
        assert len(collectors) == 0  # All require credentials

    def test_collect_all(self):
        """Test collection across all collectors."""
        config = {"collectors": {"enabled": ["http_web"]}}
        credentials = {}

        manager = CollectorManager(config, credentials)

        # Mock collector
        mock_collector = Mock()
        mock_collector.collect.return_value = [
            {"id": "finding1", "type": "web"},
            {"id": "finding2", "type": "web"},
        ]
        manager._collectors = [mock_collector]

        seeds = [{"id": "seed1", "type": "domain", "value": "example.com"}]

        findings = manager.collect_all(seeds, "2024-01-01T00:00:00Z")

        assert len(findings) == 2
        assert findings[0]["id"] == "finding1"
        mock_collector.collect.assert_called_once()

    def test_has_valid_credentials(self):
        """Test credential validation logic."""
        config = {}
        credentials = {}
        manager = CollectorManager(config, credentials)

        # Mock collector with API key
        mock_collector_with_key = Mock()
        mock_collector_with_key.api_key = "test_key"
        assert manager._has_valid_credentials(mock_collector_with_key) is True

        # Mock collector without API key
        mock_collector_without_key = Mock()
        mock_collector_without_key.api_key = None
        assert manager._has_valid_credentials(mock_collector_without_key) is False
