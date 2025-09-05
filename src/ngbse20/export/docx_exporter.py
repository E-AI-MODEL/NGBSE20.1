"""
DOCX exporter for NGBSE 20.3.
Exports findings and data to Word document format.
"""

from pathlib import Path
from typing import Any, Dict, List
from datetime import datetime

from .base import Exporter, ExportError, DataValidationError


class DOCXExporter(Exporter):
    """Exports data to DOCX format."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.template_path = config.get("docx_template_path")
        self.include_charts = config.get("include_charts", True)
        self.include_tables = config.get("include_tables", True)
    
    def export(self, data: Dict[str, Any], output_path: Path) -> bool:
        """Export data to DOCX format."""
        try:
            if not self.validate_data(data):
                raise DataValidationError("Data validation failed")
            
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Import docx here to avoid dependency issues
            try:
                from docx import Document
                from docx.shared import Inches
                from docx.enum.text import WD_ALIGN_PARAGRAPH
            except ImportError:
                self.logger.error("python-docx not installed. Install with: pip install python-docx")
                return False
            
            # Create document
            doc = Document()
            
            # Add title
            title = doc.add_heading('NGBSE 20.3 Security Analysis Report', 0)
            title.alignment = WD_ALIGN_PARAGRAPH.CENTER
            
            # Add metadata
            self._add_metadata_section(doc, data)
            
            # Add findings section
            self._add_findings_section(doc, data)
            
            # Add summary section
            self._add_summary_section(doc, data)
            
            # Add recommendations section
            self._add_recommendations_section(doc, data)
            
            # Save document
            doc.save(str(output_path))
            
            self.logger.info(f"DOCX export completed: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"DOCX export failed: {e}")
            raise ExportError(f"DOCX export failed: {e}")
    
    def get_file_extension(self) -> str:
        """Get DOCX file extension."""
        return ".docx"
    
    def get_mime_type(self) -> str:
        """Get DOCX MIME type."""
        return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate data for DOCX export."""
        if not isinstance(data, dict):
            return False
        
        findings = data.get("findings", [])
        if not isinstance(findings, list):
            return False
        
        return True  # DOCX can handle any data structure
    
    def _add_metadata_section(self, doc, data: Dict[str, Any]) -> None:
        """Add metadata section to document."""
        doc.add_heading('Report Metadata', level=1)
        
        # Add generation timestamp
        doc.add_paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Add findings count
        findings = data.get("findings", [])
        doc.add_paragraph(f"Total Findings: {len(findings)}")
        
        # Add configuration info
        config_info = data.get("config", {})
        if config_info:
            doc.add_paragraph(f"Analysis Target: {config_info.get('target', 'Unknown')}")
            doc.add_paragraph(f"Collectors Used: {', '.join(config_info.get('collectors', []))}")
    
    def _add_findings_section(self, doc, data: Dict[str, Any]) -> None:
        """Add findings section to document."""
        findings = data.get("findings", [])
        if not findings:
            doc.add_heading('Findings', level=1)
            doc.add_paragraph("No findings generated during analysis.")
            return
        
        doc.add_heading('Findings', level=1)
        
        for i, finding in enumerate(findings, 1):
            # Finding header
            finding_type = finding.get("type", "Unknown")
            severity = finding.get("severity", "Unknown")
            doc.add_heading(f"Finding {i}: {finding_type} ({severity})", level=2)
            
            # Finding details
            doc.add_paragraph(f"ID: {finding.get('id', 'N/A')}")
            doc.add_paragraph(f"Source: {finding.get('source', 'N/A')}")
            doc.add_paragraph(f"Timestamp: {finding.get('timestamp', 'N/A')}")
            
            # Description
            description = finding.get("description", "")
            if description:
                doc.add_paragraph(f"Description: {description}")
            
            # Additional details
            details = finding.get("details", {})
            if details:
                doc.add_paragraph("Additional Details:")
                for key, value in details.items():
                    doc.add_paragraph(f"  {key}: {value}", style='List Bullet')
            
            doc.add_paragraph("")  # Empty line between findings
    
    def _add_summary_section(self, doc, data: Dict[str, Any]) -> None:
        """Add summary section to document."""
        doc.add_heading('Summary', level=1)
        
        findings = data.get("findings", [])
        if not findings:
            doc.add_paragraph("No findings to summarize.")
            return
        
        # Count by severity
        severity_counts = {}
        type_counts = {}
        
        for finding in findings:
            severity = finding.get("severity", "Unknown")
            finding_type = finding.get("type", "Unknown")
            
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            type_counts[finding_type] = type_counts.get(finding_type, 0) + 1
        
        # Severity summary
        doc.add_paragraph("Findings by Severity:")
        for severity, count in severity_counts.items():
            doc.add_paragraph(f"  {severity}: {count}", style='List Bullet')
        
        # Type summary
        doc.add_paragraph("Findings by Type:")
        for finding_type, count in type_counts.items():
            doc.add_paragraph(f"  {finding_type}: {count}", style='List Bullet')
    
    def _add_recommendations_section(self, doc, data: Dict[str, Any]) -> None:
        """Add recommendations section to document."""
        doc.add_heading('Recommendations', level=1)
        
        findings = data.get("findings", [])
        if not findings:
            doc.add_paragraph("No recommendations available.")
            return
        
        # Generate basic recommendations based on findings
        high_severity_count = sum(1 for f in findings if f.get("severity", "").lower() == "high")
        
        if high_severity_count > 0:
            doc.add_paragraph(f"• Address {high_severity_count} high-severity findings immediately")
        
        doc.add_paragraph("• Review all findings and implement appropriate security measures")
        doc.add_paragraph("• Consider implementing additional monitoring for identified vulnerabilities")
        doc.add_paragraph("• Schedule regular security assessments to maintain security posture")