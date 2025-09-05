"""
Export manager for NGBSE 20.3.
Manages all export functionality and provides a unified interface.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Type

from .base import Exporter, ExportError
from .csv_exporter import CSVExporter
from .docx_exporter import DOCXExporter
from .html_exporter import HTMLExporter
from .stix_exporter import STIXExporter
from ..logging import get_logger

LOGGER = get_logger(__name__)


class ExportManager:
    """Manages all export functionality."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.exporters: Dict[str, Exporter] = {}
        self._initialize_exporters()
    
    def _initialize_exporters(self) -> None:
        """Initialize all available exporters."""
        # CSV Exporter
        self.exporters["csv"] = CSVExporter(self.config)
        
        # DOCX Exporter
        self.exporters["docx"] = DOCXExporter(self.config)
        
        # HTML Exporter
        self.exporters["html"] = HTMLExporter(self.config)
        
        # STIX Exporter
        self.exporters["stix"] = STIXExporter(self.config)
        
        LOGGER.info(f"Initialized {len(self.exporters)} exporters: {list(self.exporters.keys())}")
    
    def export(self, data: Dict[str, Any], output_path: Path, format: str) -> bool:
        """
        Export data using the specified format.
        
        Args:
            data: The data to export
            output_path: Where to save the exported file
            format: Export format (csv, docx, html, stix)
            
        Returns:
            bool: True if export successful, False otherwise
        """
        if format not in self.exporters:
            LOGGER.error(f"Unknown export format: {format}")
            return False
        
        exporter = self.exporters[format]
        
        try:
            # Ensure output path has correct extension
            if not output_path.suffix:
                output_path = output_path.with_suffix(exporter.get_file_extension())
            
            # Export data
            success = exporter.export(data, output_path)
            
            if success:
                LOGGER.info(f"Export successful: {output_path}")
            else:
                LOGGER.error(f"Export failed: {output_path}")
            
            return success
            
        except Exception as e:
            LOGGER.error(f"Export error: {e}")
            return False
    
    def export_multiple(self, data: Dict[str, Any], output_dir: Path, formats: List[str]) -> Dict[str, bool]:
        """
        Export data in multiple formats.
        
        Args:
            data: The data to export
            output_dir: Directory to save exported files
            formats: List of export formats
            
        Returns:
            Dict[str, bool]: Results for each format
        """
        results = {}
        
        for format in formats:
            if format not in self.exporters:
                LOGGER.warning(f"Skipping unknown format: {format}")
                results[format] = False
                continue
            
            # Generate output filename
            base_name = data.get("config", {}).get("target", "ngbse_report")
            output_path = output_dir / f"{base_name}.{format}"
            
            # Export
            success = self.export(data, output_path, format)
            results[format] = success
        
        return results
    
    def get_available_formats(self) -> List[str]:
        """Get list of available export formats."""
        return list(self.exporters.keys())
    
    def get_exporter_info(self, format: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific exporter."""
        if format not in self.exporters:
            return None
        
        exporter = self.exporters[format]
        return exporter.get_metadata()
    
    def get_all_exporter_info(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all exporters."""
        return {
            format: self.get_exporter_info(format)
            for format in self.exporters.keys()
        }
    
    def validate_data(self, data: Dict[str, Any], format: str) -> bool:
        """Validate data for a specific export format."""
        if format not in self.exporters:
            return False
        
        exporter = self.exporters[format]
        return exporter.validate_data(data)
    
    def register_exporter(self, name: str, exporter_class: Type[Exporter]) -> bool:
        """Register a new exporter."""
        try:
            exporter = exporter_class(self.config)
            self.exporters[name] = exporter
            LOGGER.info(f"Registered exporter: {name}")
            return True
        except Exception as e:
            LOGGER.error(f"Failed to register exporter {name}: {e}")
            return False
    
    def unregister_exporter(self, name: str) -> bool:
        """Unregister an exporter."""
        if name in self.exporters:
            del self.exporters[name]
            LOGGER.info(f"Unregistered exporter: {name}")
            return True
        return False
    
    def export_with_template(self, data: Dict[str, Any], output_path: Path, format: str, template_path: Optional[Path] = None) -> bool:
        """Export data using a custom template."""
        if format not in self.exporters:
            LOGGER.error(f"Unknown export format: {format}")
            return False
        
        exporter = self.exporters[format]
        
        # Set template path if provided
        if template_path and hasattr(exporter, 'template_path'):
            exporter.template_path = str(template_path)
        
        return self.export(data, output_path, format)
    
    def get_export_summary(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Get a summary of what can be exported."""
        findings = data.get("findings", [])
        config_info = data.get("config", {})
        
        summary = {
            "total_findings": len(findings),
            "available_formats": self.get_available_formats(),
            "export_capabilities": {},
            "recommended_formats": []
        }
        
        # Check capabilities for each format
        for format in self.exporters.keys():
            exporter = self.exporters[format]
            capabilities = {
                "can_export": exporter.validate_data(data),
                "file_extension": exporter.get_file_extension(),
                "mime_type": exporter.get_mime_type()
            }
            summary["export_capabilities"][format] = capabilities
            
            if capabilities["can_export"]:
                summary["recommended_formats"].append(format)
        
        return summary