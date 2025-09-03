"""NGBSE 20.1 package."""

__version__ = "20.2.0"

# Core modules
from .runtime.orchestrator import run_pipeline
from .cli import cli

# Collectors
from .collectors import (
    BaseCollector,
    HttpWebCollector,
    LeakIXCollector,
    ShodanCollector,
    CensysCollector,
    URLScanCollector,
    GitHubCollector,
    NewsCollector,
)

# BALLM modules
from .ballm import (
    BALLMMetaLayerGenerator,
    BlindspotInterpretationEngine,
    CuriosityGenerationEngine,
)

# Scoring and analysis
from .scoring.v18 import score_findings, compute_cai, DEFAULT as SCORE_DEFAULT
from .synth.reverse_llm import coverage_gap, recency_gap, confidence_gap
from .forecast.engine import build_forecast, aggregate_asset_scores

# Export and reporting
from .export.stix import to_stix_bundle

from .manifest import write_manifest

__all__ = [
    "__version__",
    "run_pipeline",
    "cli",
    # Collectors
    "BaseCollector",
    "HttpWebCollector",
    "LeakIXCollector",
    "ShodanCollector",
    "CensysCollector",
    "URLScanCollector",
    "GitHubCollector",
    "NewsCollector",
    # BALLM
    "BALLMMetaLayerGenerator",
    "BlindspotInterpretationEngine",
    "CuriosityGenerationEngine",
    # Scoring
    "score_findings",
    "compute_cai",
    "SCORE_DEFAULT",
    # Analysis
    "coverage_gap",
    "recency_gap",
    "confidence_gap",
    "build_forecast",
    "aggregate_asset_scores",
    # Export
    "to_stix_bundle",
    "write_manifest",
]

