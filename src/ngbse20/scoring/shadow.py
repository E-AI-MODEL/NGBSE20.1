"""Shadow mode implementation for gradual rollout of v18.1 scoring."""

from __future__ import annotations

import copy
from typing import Any

from .v18 import ScoringConfig, score_findings
from ..logging import get_logger

LOGGER = get_logger(__name__)


def score_findings_shadow(
    findings: list[dict[str, Any]], 
    cfg: ScoringConfig,
    source_trust_config: dict[str, Any] | None = None,
    rules: list[dict[str, Any]] | None = None,
    shadow_mode: bool = True
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """
    Score findings in shadow mode - compute new scores but don't apply them.
    
    Args:
        findings: List of findings to score
        cfg: Scoring configuration
        source_trust_config: Source trust configuration
        rules: Keyword rules
        shadow_mode: If True, compute both legacy and new scores for comparison
        
    Returns:
        Tuple of (scored_findings, shadow_metrics)
    """
    if not shadow_mode:
        # Normal scoring
        result = score_findings(findings, cfg, source_trust_config, rules)
        return result, {}
    
    # Shadow mode - compute both legacy and new scores
    LOGGER.info("Running in shadow mode - computing both legacy and new scores")
    
    # Create legacy config (flags off)
    legacy_cfg = copy.deepcopy(cfg)
    legacy_cfg.enable_source_trust = False
    legacy_cfg.enable_keyword_score = False
    
    # Score with legacy method
    legacy_result = score_findings(findings, legacy_cfg)
    
    # Score with new method
    new_cfg = copy.deepcopy(cfg)
    new_cfg.enable_source_trust = True
    new_cfg.enable_keyword_score = True
    
    new_result = score_findings(findings, new_cfg, source_trust_config, rules)
    
    # Compute shadow metrics
    shadow_metrics = {
        "legacy_scores": [f["score"] for f in legacy_result],
        "new_scores": [f["score"] for f in new_result],
        "score_deltas": [],
        "max_delta": 0.0,
        "avg_delta": 0.0,
        "findings_impacted": 0,
        "shadow_mode": True
    }
    
    # Calculate deltas
    for i, (legacy, new) in enumerate(zip(legacy_result, new_result)):
        delta = new["score"] - legacy["score"]
        shadow_metrics["score_deltas"].append(delta)
        shadow_metrics["max_delta"] = max(shadow_metrics["max_delta"], abs(delta))
        if abs(delta) > 0.01:  # Significant change threshold
            shadow_metrics["findings_impacted"] += 1
    
    if shadow_metrics["score_deltas"]:
        shadow_metrics["avg_delta"] = sum(abs(d) for d in shadow_metrics["score_deltas"]) / len(shadow_metrics["score_deltas"])
    
    # Log shadow metrics
    LOGGER.info(f"Shadow mode results: {shadow_metrics['findings_impacted']}/{len(findings)} findings impacted")
    LOGGER.info(f"Max score delta: {shadow_metrics['max_delta']:.3f}, Avg delta: {shadow_metrics['avg_delta']:.3f}")
    
    # Return legacy results with shadow metrics attached
    if legacy_result:
        legacy_result[0]["_shadow_metrics"] = shadow_metrics
    
    return legacy_result, shadow_metrics


def gradual_rollout_config(
    stage: str = "shadow",
    base_config: ScoringConfig | None = None
) -> ScoringConfig:
    """
    Get configuration for gradual rollout stages.
    
    Args:
        stage: Rollout stage ("shadow", "partial", "full")
        base_config: Base configuration to modify
        
    Returns:
        Configuration for the specified stage
    """
    if base_config is None:
        base_config = ScoringConfig()
    
    config = copy.deepcopy(base_config)
    
    if stage == "shadow":
        # Shadow mode - flags on but don't affect final score
        config.enable_source_trust = True
        config.enable_keyword_score = True
        config.w_source = 0.0  # Don't affect final score
        config.w_keywords = 0.0
        config.w_recency = 1.0
    elif stage == "partial":
        # Partial rollout - conservative weights
        config.enable_source_trust = True
        config.enable_keyword_score = True
        config.w_source = 0.15
        config.w_keywords = 0.10
        config.w_recency = 0.75
    elif stage == "full":
        # Full rollout - recommended weights
        config.enable_source_trust = True
        config.enable_keyword_score = True
        config.w_source = 0.25
        config.w_keywords = 0.15
        config.w_recency = 0.60
    else:
        raise ValueError(f"Unknown rollout stage: {stage}")
    
    return config