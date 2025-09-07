"""
CSV exporter for NGBSE 20.3.
Exports findings and data to CSV format for analysis.
"""

import csv
from pathlib import Path
from typing import Any, Dict, List

from .base import Exporter, ExportError, DataValidationError


class CSVExporter(Exporter):
    """Exports data to CSV format."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.delimiter = config.get("csv_delimiter", ",")
        self.quote_char = config.get("csv_quote_char", '"')
        self.encoding = config.get("csv_encoding", "utf-8")

    def export(self, data: Dict[str, Any], output_path: Path) -> bool:
        """Export data to CSV format."""
        try:
            if not self.validate_data(data):
                raise DataValidationError("Data validation failed")

            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Extract findings for CSV export
            findings = data.get("findings", [])
            if not findings:
                self.logger.warning("No findings to export")
                return False

            # Write CSV file
            with open(output_path, "w", newline="", encoding=self.encoding) as csvfile:
                if findings:
                    fieldnames = findings[0].keys()
                    writer = csv.DictWriter(
                        csvfile, fieldnames=fieldnames, delimiter=self.delimiter, quotechar=self.quote_char
                    )

                    writer.writeheader()
                    writer.writerows(findings)

            self.logger.info(f"CSV export completed: {output_path}")
            return True

        except Exception as e:
            self.logger.error(f"CSV export failed: {e}")
            raise ExportError(f"CSV export failed: {e}")

    def get_file_extension(self) -> str:
        """Get CSV file extension."""
        return ".csv"

    def get_mime_type(self) -> str:
        """Get CSV MIME type."""
        return "text/csv"

    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate data for CSV export."""
        if not isinstance(data, dict):
            return False

        findings = data.get("findings", [])
        if not isinstance(findings, list):
            return False

        if not findings:
            return True  # Empty findings are valid

        # Check if all findings are dictionaries
        return all(isinstance(finding, dict) for finding in findings)

    def export_findings_summary(self, data: Dict[str, Any], output_path: Path) -> bool:
        """Export a summary of findings to CSV."""
        try:
            findings = data.get("findings", [])
            if not findings:
                return False

            # Create summary data
            summary_data = []
            for finding in findings:
                summary = {
                    "id": finding.get("id", ""),
                    "type": finding.get("type", ""),
                    "severity": finding.get("severity", ""),
                    "source": finding.get("source", ""),
                    "timestamp": finding.get("timestamp", ""),
                    "description": (
                        finding.get("description", "")[:100] + "..."
                        if len(finding.get("description", "")) > 100
                        else finding.get("description", "")
                    ),
                }
                summary_data.append(summary)

            # Export summary
            summary_data_dict = {"findings": summary_data}
            return self.export(summary_data_dict, output_path)

        except Exception as e:
            self.logger.error(f"CSV summary export failed: {e}")
            return False
