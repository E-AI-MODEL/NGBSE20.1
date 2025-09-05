"""
Unit tests for NGBSE 20.3 export system.
Tests all export modules and functionality.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from ngbse20.export.base import Exporter, ExportError, DataValidationError
from ngbse20.export.csv_exporter import CSVExporter
from ngbse20.export.docx_exporter import DOCXExporter
from ngbse20.export.html_exporter import HTMLExporter
from ngbse20.export.stix_exporter import STIXExporter
from ngbse20.export.export_manager import ExportManager


class TestExporterBase:
    """Test base exporter functionality."""
    
    def test_exporter_interface(self):
        """Test exporter interface methods."""
        # Mock exporter implementation
        class MockExporter(Exporter):
            def export(self, data, output_path):
                return True
            
            def get_file_extension(self):
                return ".test"
            
            def get_mime_type(self):
                return "text/test"
            
            def validate_data(self, data):
                return True
        
        exporter = MockExporter({})
        
        assert exporter.get_file_extension() == ".test"
        assert exporter.get_mime_type() == "text/test"
        assert exporter.validate_data({}) is True
        assert exporter.export({}, Path("/tmp/test")) is True
    
    def test_export_error(self):
        """Test export error handling."""
        with pytest.raises(ExportError):
            raise ExportError("Test error")
        
        with pytest.raises(DataValidationError):
            raise DataValidationError("Validation error")


class TestCSVExporter:
    """Test CSV exporter functionality."""
    
    def test_csv_exporter_initialization(self):
        """Test CSV exporter initialization."""
        config = {
            "csv_delimiter": ";",
            "csv_quote_char": "'",
            "csv_encoding": "latin-1"
        }
        exporter = CSVExporter(config)
        
        assert exporter.delimiter == ";"
        assert exporter.quote_char == "'"
        assert exporter.encoding == "latin-1"
    
    def test_csv_exporter_defaults(self):
        """Test CSV exporter default values."""
        exporter = CSVExporter({})
        
        assert exporter.delimiter == ","
        assert exporter.quote_char == '"'
        assert exporter.encoding == "utf-8"
    
    def test_csv_export_success(self):
        """Test successful CSV export."""
        exporter = CSVExporter({})
        
        data = {
            "findings": [
                {"id": "1", "type": "vulnerability", "severity": "high"},
                {"id": "2", "type": "threat", "severity": "medium"}
            ]
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test.csv"
            result = exporter.export(data, output_path)
            
            assert result is True
            assert output_path.exists()
            
            # Verify CSV content
            content = output_path.read_text()
            assert "id,type,severity" in content
            assert "1,vulnerability,high" in content
    
    def test_csv_export_empty_findings(self):
        """Test CSV export with empty findings."""
        exporter = CSVExporter({})
        
        data = {"findings": []}
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test.csv"
            result = exporter.export(data, output_path)
            
            assert result is False  # Should fail for empty findings
    
    def test_csv_export_invalid_data(self):
        """Test CSV export with invalid data."""
        exporter = CSVExporter({})
        
        data = {"findings": "not_a_list"}
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test.csv"
            
            with pytest.raises(DataValidationError):
                exporter.export(data, output_path)
    
    def test_csv_export_findings_summary(self):
        """Test CSV export findings summary."""
        exporter = CSVExporter({})
        
        data = {
            "findings": [
                {"id": "1", "type": "vulnerability", "severity": "high", "description": "A" * 200}
            ]
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "summary.csv"
            result = exporter.export_findings_summary(data, output_path)
            
            assert result is True
            assert output_path.exists()
            
            # Verify summary content
            content = output_path.read_text()
            assert "id,type,severity,source,timestamp,description" in content
            assert "1,vulnerability,high" in content


class TestHTMLExporter:
    """Test HTML exporter functionality."""
    
    def test_html_exporter_initialization(self):
        """Test HTML exporter initialization."""
        config = {
            "html_theme": "dark",
            "html_title": "Custom Report",
            "include_charts": False
        }
        exporter = HTMLExporter(config)
        
        assert exporter.theme == "dark"
        assert exporter.title == "Custom Report"
        assert exporter.include_charts is False
    
    def test_html_export_success(self):
        """Test successful HTML export."""
        exporter = HTMLExporter({})
        
        data = {
            "findings": [
                {"id": "1", "type": "vulnerability", "severity": "high", "description": "Test finding"}
            ],
            "config": {"target": "test.example.com"}
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test.html"
            result = exporter.export(data, output_path)
            
            assert result is True
            assert output_path.exists()
            
            # Verify HTML content
            content = output_path.read_text()
            assert "<!DOCTYPE html>" in content
            assert "NGBSE 20.3 Security Analysis Report" in content
            assert "test.example.com" in content
            assert "vulnerability" in content
    
    def test_html_export_empty_findings(self):
        """Test HTML export with empty findings."""
        exporter = HTMLExporter({})
        
        data = {"findings": [], "config": {"target": "test.example.com"}}
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test.html"
            result = exporter.export(data, output_path)
            
            assert result is True
            assert output_path.exists()
            
            content = output_path.read_text()
            assert "No findings generated during analysis" in content


class TestDOCXExporter:
    """Test DOCX exporter functionality."""
    
    def test_docx_exporter_initialization(self):
        """Test DOCX exporter initialization."""
        config = {
            "include_charts": False,
            "include_tables": False,
            "docx_template_path": "/path/to/template.docx"
        }
        exporter = DOCXExporter(config)
        
        assert exporter.include_charts is False
        assert exporter.include_tables is False
        assert exporter.template_path == "/path/to/template.docx"
    
    @patch('ngbse20.export.docx_exporter.Document')
    def test_docx_export_success(self, mock_document):
        """Test successful DOCX export."""
        # Mock Document class
        mock_doc = Mock()
        mock_document.return_value = mock_doc
        
        exporter = DOCXExporter({})
        
        data = {
            "findings": [
                {"id": "1", "type": "vulnerability", "severity": "high", "description": "Test finding"}
            ],
            "config": {"target": "test.example.com"}
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test.docx"
            result = exporter.export(data, output_path)
            
            assert result is True
            mock_doc.save.assert_called_once_with(str(output_path))
    
    def test_docx_export_missing_dependency(self):
        """Test DOCX export with missing python-docx dependency."""
        exporter = DOCXExporter({})
        
        data = {"findings": [], "config": {"target": "test.example.com"}}
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test.docx"
            
            with patch('ngbse20.export.docx_exporter.Document', side_effect=ImportError):
                result = exporter.export(data, output_path)
                assert result is False


class TestSTIXExporter:
    """Test STIX exporter functionality."""
    
    def test_stix_exporter_initialization(self):
        """Test STIX exporter initialization."""
        config = {
            "stix_version": "2.0",
            "include_indicators": False,
            "include_observables": False
        }
        exporter = STIXExporter(config)
        
        assert exporter.stix_version == "2.0"
        assert exporter.include_indicators is False
        assert exporter.include_observables is False
    
    def test_stix_export_missing_dependency(self):
        """Test STIX export with missing stix2 dependency."""
        exporter = STIXExporter({})
        
        data = {"findings": [], "config": {"target": "test.example.com"}}
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test.json"
            
            with patch('ngbse20.export.stix_exporter.stix2', side_effect=ImportError):
                result = exporter.export(data, output_path)
                assert result is False
    
    @patch('ngbse20.export.stix_exporter.stix2')
    def test_stix_export_success(self, mock_stix2):
        """Test successful STIX export."""
        # Mock stix2 objects
        mock_identity = Mock()
        mock_bundle = Mock()
        mock_bundle.serialize.return_value = '{"type": "bundle"}'
        
        mock_stix2.Identity.return_value = mock_identity
        mock_stix2.Bundle.return_value = mock_bundle
        
        exporter = STIXExporter({})
        
        data = {
            "findings": [
                {"id": "1", "type": "ip", "value": "192.168.1.1", "severity": "high"}
            ],
            "config": {"target": "test.example.com"}
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test.json"
            result = exporter.export(data, output_path)
            
            assert result is True
            assert output_path.exists()
            
            content = output_path.read_text()
            assert "bundle" in content


class TestExportManager:
    """Test export manager functionality."""
    
    def test_export_manager_initialization(self):
        """Test export manager initialization."""
        config = {
            "csv_delimiter": ";",
            "html_theme": "dark"
        }
        manager = ExportManager(config)
        
        assert "csv" in manager.exporters
        assert "html" in manager.exporters
        assert "docx" in manager.exporters
        assert "stix" in manager.exporters
    
    def test_export_manager_available_formats(self):
        """Test getting available export formats."""
        manager = ExportManager({})
        formats = manager.get_available_formats()
        
        assert "csv" in formats
        assert "html" in formats
        assert "docx" in formats
        assert "stix" in formats
    
    def test_export_manager_export_single(self):
        """Test single format export."""
        manager = ExportManager({})
        
        data = {
            "findings": [
                {"id": "1", "type": "vulnerability", "severity": "high"}
            ],
            "config": {"target": "test.example.com"}
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test.csv"
            result = manager.export(data, output_path, "csv")
            
            assert result is True
            assert output_path.exists()
    
    def test_export_manager_export_multiple(self):
        """Test multiple format export."""
        manager = ExportManager({})
        
        data = {
            "findings": [
                {"id": "1", "type": "vulnerability", "severity": "high"}
            ],
            "config": {"target": "test.example.com"}
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            results = manager.export_multiple(data, output_dir, ["csv", "html"])
            
            assert "csv" in results
            assert "html" in results
            assert results["csv"] is True
            assert results["html"] is True
    
    def test_export_manager_unknown_format(self):
        """Test export with unknown format."""
        manager = ExportManager({})
        
        data = {"findings": []}
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test.unknown"
            result = manager.export(data, output_path, "unknown")
            
            assert result is False
    
    def test_export_manager_validate_data(self):
        """Test data validation."""
        manager = ExportManager({})
        
        valid_data = {"findings": []}
        invalid_data = {"findings": "not_a_list"}
        
        assert manager.validate_data(valid_data, "csv") is True
        assert manager.validate_data(invalid_data, "csv") is False
    
    def test_export_manager_get_exporter_info(self):
        """Test getting exporter information."""
        manager = ExportManager({})
        
        info = manager.get_exporter_info("csv")
        assert info is not None
        assert "name" in info
        assert "extension" in info
        assert "mime_type" in info
        
        unknown_info = manager.get_exporter_info("unknown")
        assert unknown_info is None
    
    def test_export_manager_get_export_summary(self):
        """Test getting export summary."""
        manager = ExportManager({})
        
        data = {
            "findings": [
                {"id": "1", "type": "vulnerability", "severity": "high"}
            ],
            "config": {"target": "test.example.com"}
        }
        
        summary = manager.get_export_summary(data)
        
        assert "total_findings" in summary
        assert "available_formats" in summary
        assert "export_capabilities" in summary
        assert "recommended_formats" in summary
        
        assert summary["total_findings"] == 1
        assert "csv" in summary["available_formats"]
        assert "csv" in summary["recommended_formats"]


if __name__ == "__main__":
    pytest.main([__file__])