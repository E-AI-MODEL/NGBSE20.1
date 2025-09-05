"""NGBSE 20.1 package."""

__version__ = "20.2.1"

# BALLM modules (optional - requires LLM dependencies)
try:
    from .ballm import (
        BALLMMetaLayerGenerator,
        BlindspotInterpretationEngine,
        CuriosityGenerationEngine,
    )
    BALLM_AVAILABLE = True
except ImportError:
    BALLM_AVAILABLE = False
    # Create dummy classes when BALLM is not available
    class BALLMMetaLayerGenerator:
        pass
    class BlindspotInterpretationEngine:
        pass
    class CuriosityGenerationEngine:
        pass
# CLI (optional - requires click dependency)
try:
    from .cli import cli
    CLI_AVAILABLE = True
except ImportError:
    CLI_AVAILABLE = False
    cli = None

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

# Synthesis modules (optional - requires LLM dependencies)
try:
    from .synth.reverse_llm import confidence_gap, coverage_gap, recency_gap
    SYNTH_AVAILABLE = True
except ImportError:
    SYNTH_AVAILABLE = False
    def confidence_gap(*args, **kwargs):
        return 0.0
    def coverage_gap(*args, **kwargs):
        return 0.0
    def recency_gap(*args, **kwargs):
        return 0.0

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
