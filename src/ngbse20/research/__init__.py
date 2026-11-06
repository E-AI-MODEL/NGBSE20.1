"""Analyse van teksten en onderzoek, los van OSINT-collectors."""

from .document_blindspots import BALLMDocumentProposer, analyze_document

__all__ = ["BALLMDocumentProposer", "analyze_document"]
