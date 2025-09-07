"""
Base exporter interface for NGBSE 20.3.
Defines the contract for all export implementations.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pathlib import Path

from ..logging import get_logger

LOGGER = get_logger(__name__)


class Exporter(ABC):
    """Abstract base class for all exporters."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = LOGGER

    @abstractmethod
    def export(self, data: Dict[str, Any], output_path: Path) -> bool:
        """
        Export data to the specified output path.

        Args:
            data: The data to export
            output_path: Where to save the exported file

        Returns:
            bool: True if export successful, False otherwise
        """
        pass

    @abstractmethod
    def get_file_extension(self) -> str:
        """Get the file extension for this exporter."""
        pass

    @abstractmethod
    def get_mime_type(self) -> str:
        """Get the MIME type for this exporter."""
        pass

    @abstractmethod
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """
        Validate that the data is suitable for this exporter.

        Args:
            data: The data to validate

        Returns:
            bool: True if data is valid, False otherwise
        """
        pass

    def get_metadata(self) -> Dict[str, Any]:
        """Get exporter metadata."""
        return {
            "name": self.__class__.__name__,
            "extension": self.get_file_extension(),
            "mime_type": self.get_mime_type(),
            "description": self.__doc__ or "",
        }


class ExportError(Exception):
    """Exception raised when export operations fail."""

    pass


class DataValidationError(ExportError):
    """Exception raised when data validation fails."""

    pass


class ExportPathError(ExportError):
    """Exception raised when output path operations fail."""

    pass
