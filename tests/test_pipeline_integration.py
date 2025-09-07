"""
Integration tests for NGBSE 20.3 pipeline.
Tests pipeline integration with modular export and collector systems.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from ngbse20.runtime.orchestrator import PipelineOrchestrator
from ngbse20.export.export_manager import ExportManager
from ngbse20.runtime.collector_manager import CollectorManager


class TestPipelineIntegration:
    """Test pipeline integration with modular systems."""

    @patch("ngbse20.runtime.orchestrator.ConfigLoader")
    def test_pipeline_orchestrator_initialization(self, mock_config_loader):
        """Test pipeline orchestrator initialization with new systems."""
        # Mock config loader
        mock_loader = Mock()
        mock_config_loader.return_value = mock_loader

        # Mock config
        mock_config = Mock()
        mock_config.__dict__ = {
            "output_dir": "output",
            "allowlist": ["*"],
            "export": {"formats": ["csv", "html"], "output_dir": "output"},
        }
        mock_loader.load_config.return_value = mock_config
        mock_loader.get_credentials.return_value = {"shodan": "test_key"}

        # Mock pipeline stages
        with patch("ngbse20.runtime.orchestrator.PipelineStages"):
            orchestrator = PipelineOrchestrator()

            assert hasattr(orchestrator, "export_manager")
            assert hasattr(orchestrator, "collector_manager")
            assert isinstance(orchestrator.export_manager, ExportManager)
            assert isinstance(orchestrator.collector_manager, CollectorManager)

    @patch("ngbse20.runtime.orchestrator.ConfigLoader")
    def test_pipeline_run_with_modular_export(self, mock_config_loader):
        """Test pipeline run with modular export system."""
        # Mock config loader
        mock_loader = Mock()
        mock_config_loader.return_value = mock_loader

        # Mock config
        mock_config = Mock()
        mock_config.__dict__ = {
            "output_dir": "output",
            "allowlist": ["*"],
            "export": {"formats": ["csv", "html"], "output_dir": "output"},
        }
        mock_loader.load_config.return_value = mock_config
        mock_loader.get_credentials.return_value = {}
        mock_loader.load_seeds.return_value = []
        mock_loader.load_rules.return_value = []

        # Mock pipeline stages
        with patch("ngbse20.runtime.orchestrator.PipelineStages") as mock_stages:
            mock_stages_instance = Mock()
            mock_stages.return_value = mock_stages_instance

            # Mock all pipeline stage methods
            mock_stages_instance.validate_stage.return_value = {"status": "ok", "trace": {}}
            mock_stages_instance.collect_stage.return_value = {"findings": [], "trace": {}}
            mock_stages_instance.rules_stage.return_value = {"trace": {}}
            mock_stages_instance.scoring_stage.return_value = {"scored_findings": [], "trace": {}}
            mock_stages_instance.forecast_stage.return_value = {
                "asset_scores": [],
                "forecast": [],
                "history_path": "history.json",
                "trace": {},
            }
            mock_stages_instance.seed_proposal_stage.return_value = {"next_seeds": [], "trace": {}}
            mock_stages_instance.blindspot_analysis_stage.return_value = {"blindspots": [], "trace": {}}
            mock_stages_instance.ballm_stage.return_value = {"meta_layer": {}, "trace": {}}
            mock_stages_instance.scenario_stage.return_value = {"scenarios": [], "trace": {}}
            mock_stages_instance.brief_stage.return_value = {"brief": "Test brief"}
            mock_stages_instance.export_stage.return_value = {
                "cai": 0.5,
                "bundle": {},
                "output_files": {"findings": "findings.json", "stix_bundle": "bundle.json"},
                "trace": {},
            }
            mock_stages_instance.report_stage.return_value = {"report_path": "report.docx", "trace": {}}

            orchestrator = PipelineOrchestrator()

            # Mock collector manager
            orchestrator.collector_manager.build_collectors = Mock(return_value=[])

            # Mock export manager
            orchestrator.export_manager.export_multiple = Mock(return_value={"csv": True, "html": True})

            result = orchestrator.run_pipeline()

            assert result["status"] == "ok"
            assert "cai" in result
            assert "findings" in result
            assert "traces" in result

    def test_export_data_method(self):
        """Test export_data method in orchestrator."""
        with patch("ngbse20.runtime.orchestrator.ConfigLoader"):
            with patch("ngbse20.runtime.orchestrator.PipelineStages"):
                orchestrator = PipelineOrchestrator()

                # Mock export manager
                orchestrator.export_manager.export = Mock(return_value=True)

                data = {"findings": [], "config": {"target": "test.example.com"}}
                output_path = Path("/tmp/test.csv")

                result = orchestrator.export_data(data, output_path, "csv")

                assert result is True
                orchestrator.export_manager.export.assert_called_once_with(data, output_path, "csv")

    def test_get_available_export_formats(self):
        """Test get_available_export_formats method."""
        with patch("ngbse20.runtime.orchestrator.ConfigLoader"):
            with patch("ngbse20.runtime.orchestrator.PipelineStages"):
                orchestrator = PipelineOrchestrator()

                # Mock export manager
                orchestrator.export_manager.get_available_formats = Mock(return_value=["csv", "html", "docx"])

                formats = orchestrator.get_available_export_formats()

                assert "csv" in formats
                assert "html" in formats
                assert "docx" in formats

    def test_get_export_summary(self):
        """Test get_export_summary method."""
        with patch("ngbse20.runtime.orchestrator.ConfigLoader"):
            with patch("ngbse20.runtime.orchestrator.PipelineStages"):
                orchestrator = PipelineOrchestrator()

                # Mock export manager
                mock_summary = {
                    "total_findings": 5,
                    "available_formats": ["csv", "html"],
                    "recommended_formats": ["csv", "html"],
                }
                orchestrator.export_manager.get_export_summary = Mock(return_value=mock_summary)

                data = {"findings": [{"id": "1"}] * 5}
                summary = orchestrator.get_export_summary(data)

                assert summary["total_findings"] == 5
                assert "csv" in summary["available_formats"]

    @patch("ngbse20.runtime.orchestrator.ConfigLoader")
    def test_modular_export_stage_success(self, mock_config_loader):
        """Test successful modular export stage."""
        # Mock config loader
        mock_loader = Mock()
        mock_config_loader.return_value = mock_loader

        # Mock config
        mock_config = Mock()
        mock_config.__dict__ = {
            "output_dir": "output",
            "allowlist": ["*"],
            "export": {"formats": ["csv", "html"], "output_dir": "output"},
        }
        mock_loader.load_config.return_value = mock_config
        mock_loader.get_credentials.return_value = {}

        with patch("ngbse20.runtime.orchestrator.PipelineStages"):
            orchestrator = PipelineOrchestrator()

            # Mock export manager
            orchestrator.export_manager.export_multiple = Mock(return_value={"csv": True, "html": True})

            # Test data
            scored_findings = [{"id": "1", "type": "vulnerability", "severity": "high"}]
            brief = "Test brief"
            blindspots = []
            forecast = []
            scenarios = []
            ballm_meta_layer = {}
            bundle = {}
            next_seeds = []
            traces = [{"timestamp": "2024-01-01T00:00:00Z"}]

            result = orchestrator._run_modular_export_stage(
                scored_findings=scored_findings,
                brief=brief,
                blindspots=blindspots,
                forecast=forecast,
                scenarios=scenarios,
                ballm_meta_layer=ballm_meta_layer,
                bundle=bundle,
                next_seeds=next_seeds,
                traces=traces,
            )

            assert result["status"] == "completed"
            assert "output_files" in result
            assert "export_results" in result
            assert result["export_results"]["csv"] is True
            assert result["export_results"]["html"] is True

    @patch("ngbse20.runtime.orchestrator.ConfigLoader")
    def test_modular_export_stage_failure(self, mock_config_loader):
        """Test modular export stage failure."""
        # Mock config loader
        mock_loader = Mock()
        mock_config_loader.return_value = mock_loader

        # Mock config
        mock_config = Mock()
        mock_config.__dict__ = {
            "output_dir": "output",
            "allowlist": ["*"],
            "export": {"formats": ["csv", "html"], "output_dir": "output"},
        }
        mock_loader.load_config.return_value = mock_config
        mock_loader.get_credentials.return_value = {}

        with patch("ngbse20.runtime.orchestrator.PipelineStages"):
            orchestrator = PipelineOrchestrator()

            # Mock export manager to raise exception
            orchestrator.export_manager.export_multiple = Mock(side_effect=Exception("Export failed"))

            # Test data
            scored_findings = []
            brief = "Test brief"
            blindspots = []
            forecast = []
            scenarios = []
            ballm_meta_layer = {}
            bundle = {}
            next_seeds = []
            traces = []

            result = orchestrator._run_modular_export_stage(
                scored_findings=scored_findings,
                brief=brief,
                blindspots=blindspots,
                forecast=forecast,
                scenarios=scenarios,
                ballm_meta_layer=ballm_meta_layer,
                bundle=bundle,
                next_seeds=next_seeds,
                traces=traces,
            )

            assert result["status"] == "failed"
            assert "error" in result
            assert "Export failed" in result["error"]


class TestExportManagerIntegration:
    """Test export manager integration."""

    def test_export_manager_with_config(self):
        """Test export manager with configuration."""
        config = {"csv_delimiter": ";", "html_theme": "dark", "stix_version": "2.0"}

        manager = ExportManager(config)

        # Test that configuration is passed to exporters
        csv_exporter = manager.exporters["csv"]
        assert csv_exporter.delimiter == ";"

        html_exporter = manager.exporters["html"]
        assert html_exporter.theme == "dark"

        stix_exporter = manager.exporters["stix"]
        assert stix_exporter.stix_version == "2.0"

    def test_export_manager_register_exporter(self):
        """Test registering custom exporter."""
        manager = ExportManager({})

        # Mock custom exporter
        class CustomExporter:
            def __init__(self, config):
                self.config = config

            def export(self, data, output_path):
                return True

            def get_file_extension(self):
                return ".custom"

            def get_mime_type(self):
                return "application/custom"

            def validate_data(self, data):
                return True

        result = manager.register_exporter("custom", CustomExporter)

        assert result is True
        assert "custom" in manager.exporters
        assert manager.exporters["custom"].get_file_extension() == ".custom"

    def test_export_manager_unregister_exporter(self):
        """Test unregistering exporter."""
        manager = ExportManager({})

        # Initially has default exporters
        assert "csv" in manager.exporters

        result = manager.unregister_exporter("csv")

        assert result is True
        assert "csv" not in manager.exporters

    def test_export_manager_export_with_template(self):
        """Test export with custom template."""
        manager = ExportManager({})

        data = {"findings": [], "config": {"target": "test.example.com"}}
        output_path = Path("/tmp/test.html")
        template_path = Path("/tmp/template.html")

        # Mock HTML exporter
        html_exporter = manager.exporters["html"]
        html_exporter.template_path = None

        with patch.object(html_exporter, "export", return_value=True) as mock_export:
            result = manager.export_with_template(data, output_path, "html", template_path)

            assert result is True
            assert html_exporter.template_path == str(template_path)
            mock_export.assert_called_once_with(data, output_path)


class TestCollectorManagerIntegration:
    """Test collector manager integration."""

    def test_collector_manager_with_external_collectors(self):
        """Test collector manager with external collectors."""
        config = {
            "external_collectors": [
                {"name": "custom_collector", "module_path": "/path/to/collector.py", "class_name": "CustomCollector"}
            ]
        }
        credentials = {}

        with patch.object(CollectorManager, "_load_external_collectors") as mock_load:
            manager = CollectorManager(config, credentials)

            # Verify external collectors are loaded
            mock_load.assert_called_once()

    def test_collector_manager_plugin_directory(self):
        """Test collector manager with plugin directory."""
        config = {"collector_manager": {"plugin_directory": "/path/to/plugins", "auto_discovery": True}}
        credentials = {}

        manager = CollectorManager(config, credentials)

        # Verify plugin directory is set
        assert manager.config.get("collector_manager", {}).get("plugin_directory") == "/path/to/plugins"


if __name__ == "__main__":
    pytest.main([__file__])
