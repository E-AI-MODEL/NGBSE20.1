"""NGBSE 20.1 package."""

__version__ = "20.2.1"

# BALLM modules
from .ballm import (
    BALLMMetaLayerGenerator,
    BlindspotInterpretationEngine,
    CuriosityGenerationEngine,
)
from .cli import cli

# Collectors
from .collectors import (
    BaseCollector,
    CensysCollector,
    GitHubCollector,
    HttpWebCollector,
    LeakIXCollector,
    NewsCollector,
    ShodanCollector,
    URLScanCollector,
)

# Export and reporting
from .export.stix import to_stix_bundle
from .forecast.engine import aggregate_asset_scores, build_forecast
from .manifest import write_manifest

# Core modules
from .runtime.orchestrator import run_pipeline

# Scoring and analysis
from .scoring.v18 import DEFAULT as SCORE_DEFAULT
from .scoring.v18 import compute_cai, score_findings
from .synth.reverse_llm import confidence_gap, coverage_gap, recency_gap

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
