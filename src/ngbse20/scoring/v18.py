"""Simple scoring engine v18."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

from ..logging import get_logger

LOGGER = get_logger(__name__)


@dataclass
class ScoringConfig:
    half_life_days: int = 15
    weights: dict[str, float] = field(
        default_factory=lambda: {
            "source": 0.30,
            "keywords": 0.30,
            "recency": 0.40,
        }
    )
    extras: dict[str, float] = field(
        default_factory=lambda: {
            "novelty": 0.10,
            "symbolic_consistency": 0.15,
            "contradiction_penalty": 0.15,
            "abduction_value": 0.10,
        }
    )
    # New flags for v18.1
    enable_source_trust: bool = False
    enable_keyword_score: bool = False
    w_source: float = 0.25
    w_keywords: float = 0.15
    w_recency: float = 0.60
    keyword_normalization_max: float = 10.0
    scoring_version: str = "v18.1"


DEFAULT = ScoringConfig()


def _recency_score(ts: datetime, half_life_days: int) -> float:
    now = datetime.now(timezone.utc)
    age_days = max(0.0, (now - ts).total_seconds() / 86400.0)
    return 0.5 ** (age_days / float(half_life_days))


def _clamp(x: float) -> float:
    return max(0.0, min(1.0, float(x)))


def _source_score(f: dict[str, Any]) -> float:
    try:
        return float(f.get("metrics", {}).get("source", 0))
    except (ValueError, TypeError) as e:
        LOGGER.warning(f"Failed to parse source score: {e}")
        return 0.0


def _keyword_score(f: dict[str, Any]) -> float:
    try:
        return float(f.get("metrics", {}).get("keywords", 0))
    except (ValueError, TypeError) as e:
        LOGGER.warning(f"Failed to parse keyword score: {e}")
        return 0.0


def _extract_domain(url: str) -> str | None:
    """Extract domain from URL."""
    try:
        parsed = urlparse(url)
        return parsed.netloc.lower()
    except Exception:
        return None


def _source_trust_score(f: dict[str, Any], source_trust_config: dict[str, Any] | None) -> float:
    """Compute source trust score based on domain trust levels."""
    if not source_trust_config:
        return 0.0
    
    url = f.get("url", "")
    domain = _extract_domain(url)
    if not domain:
        return source_trust_config.get("default_trust_level", 0.5)
    
    domains = source_trust_config.get("domains", {})
    domain_config = domains.get(domain, {})
    return domain_config.get("trust_level", source_trust_config.get("default_trust_level", 0.5))


def _keyword_pattern_score(f: dict[str, Any], rules: list[dict[str, Any]]) -> tuple[float, list[dict[str, Any]]]:
    """Compute keyword pattern score and return contributors."""
    if not rules:
        return 0.0, []
    
    # Build searchable text
    searchable_fields = ["title", "description", "content", "summary", "text"]
    searchable_text = ""
    for field_name in searchable_fields:
        value = f.get(field_name, "")
        if isinstance(value, str):
            searchable_text += " " + value.lower()
    
    searchable_text = searchable_text.strip()
    if not searchable_text:
        return 0.0, []
    
    # Precompile patterns
    compiled_rules = []
    for rule in rules:
        if not rule.get("enabled", True):
            continue
        try:
            pattern = re.compile(rule["pattern"], re.IGNORECASE)
            compiled_rules.append((pattern, rule))
        except re.error as e:
            LOGGER.warning(f"Invalid regex pattern in rule {rule.get('id', 'unknown')}: {e}")
            continue
    
    # Compute scores
    total_score = 0.0
    contributors = []
    
    for pattern, rule in compiled_rules:
        matches = pattern.findall(searchable_text)
        if matches:
            weight = rule.get("weight", 1.0)
            score = len(matches) * weight
            total_score += score
            
            contributors.append({
                "rule_id": rule.get("id", "unknown"),
                "rule_name": rule.get("name", "Unknown"),
                "weight": weight,
                "matches": len(matches),
                "score": score
            })
    
    return total_score, contributors


def compute_cai(traces: list[dict[str, Any]], cfg: dict[str, Any] | None = None) -> float:
    if not traces:
        return 0.0
    w = {"trace": 0.4, "transparency": 0.3, "blindspot": 0.3}
    if isinstance(cfg, dict) and "cai_weights" in cfg:
        w.update(cfg["cai_weights"])
    trs, trp, blind = [], [], 0
    for e in traces:
        rub = e.get("rubric") or {}
        if "reasoning_trace" in rub:
            trs.append(float(rub.get("reasoning_trace", 0)))
        if "transparency" in rub:
            trp.append(float(rub.get("transparency", 0)))
        if e.get("component") == "rules":
            acts = (e.get("output") or {}).get("actions", [])
            if any(a.get("type") in ("warning_flag", "hard_block") for a in acts):
                blind += 1
    n = max(1, len(traces))
    blind_rate = blind / n

    def mean(xs: list[float]) -> float:
        return (sum(xs) / len(xs)) if xs else 0.0

    return _clamp(w["trace"] * mean(trs) + w["transparency"] * mean(trp) + w["blindspot"] * blind_rate)


def _parse_ts(ts_raw: Any) -> datetime | None:
    if ts_raw is None:
        return None
    if isinstance(ts_raw, datetime):
        return ts_raw
    if isinstance(ts_raw, str):
        try:
            return datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
        except (ValueError, TypeError) as e:
            LOGGER.warning(f"Failed to parse timestamp '{ts_raw}': {e}")
            return None
    return None


def score_findings(
    findings: list[dict[str, Any]], 
    cfg: ScoringConfig = DEFAULT,
    source_trust_config: dict[str, Any] | None = None,
    rules: list[dict[str, Any]] | None = None
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    LOGGER.debug(f"Scoring {len(findings)} findings with config: {cfg}")
    
    # Metrics collection
    metrics = {
        "total_findings": len(findings),
        "source_trust_enabled": cfg.enable_source_trust,
        "keyword_score_enabled": cfg.enable_keyword_score,
        "scoring_version": cfg.scoring_version,
        "source_trust_scores": [],
        "keyword_scores": [],
        "processing_time_ms": 0
    }
    
    import time
    start_time = time.time()

    for f in findings:
        m = dict(f.get("metrics", {}))
        ts_dt = _parse_ts(f.get("timestamp"))
        rec = _recency_score(ts_dt, cfg.half_life_days) if ts_dt else 0.0
        
        # Legacy scoring (when flags are off)
        if not cfg.enable_source_trust and not cfg.enable_keyword_score:
            base = (
                cfg.weights.get("source", 0) * _clamp(_source_score(f))
                + cfg.weights.get("keywords", 0) * _clamp(_keyword_score(f))
                + cfg.weights.get("recency", 0) * _clamp(rec)
            )
            extras = (
                cfg.extras.get("novelty", 0) * _clamp(m.get("novelty", 0))
                + cfg.extras.get("symbolic_consistency", 0) * _clamp(m.get("symbolic_consistency", 0))
                - cfg.extras.get("contradiction_penalty", 0) * _clamp(m.get("contradiction_penalty", 0))
                + cfg.extras.get("abduction_value", 0) * _clamp(m.get("abduction_value", 0))
            )
            score = _clamp(base + extras)
            f["score_breakdown"] = {"base": base, "extras": extras, "recency": rec}
            f["score"] = score
            f["scoring_version"] = cfg.scoring_version
        else:
            # New v18.1 scoring with S_s and S_k
            s_source = _source_trust_score(f, source_trust_config) if cfg.enable_source_trust else 0.0
            s_keywords_raw, contributors = _keyword_pattern_score(f, rules or []) if cfg.enable_keyword_score else (0.0, [])
            s_keywords = _clamp(s_keywords_raw / cfg.keyword_normalization_max) if cfg.enable_keyword_score else 0.0
            
            # Collect metrics
            if cfg.enable_source_trust:
                metrics["source_trust_scores"].append(s_source)
            if cfg.enable_keyword_score:
                metrics["keyword_scores"].append(s_keywords)
            
            # Use new weights when flags are enabled
            if cfg.enable_source_trust or cfg.enable_keyword_score:
                w_source = cfg.w_source
                w_keywords = cfg.w_keywords
                w_recency = cfg.w_recency
            else:
                w_source = cfg.weights.get("source", 0)
                w_keywords = cfg.weights.get("keywords", 0)
                w_recency = cfg.weights.get("recency", 0)
            
            base = (
                w_source * _clamp(s_source)
                + w_keywords * _clamp(s_keywords)
                + w_recency * _clamp(rec)
            )
            extras = (
                cfg.extras.get("novelty", 0) * _clamp(m.get("novelty", 0))
                + cfg.extras.get("symbolic_consistency", 0) * _clamp(m.get("symbolic_consistency", 0))
                - cfg.extras.get("contradiction_penalty", 0) * _clamp(m.get("contradiction_penalty", 0))
                + cfg.extras.get("abduction_value", 0) * _clamp(m.get("abduction_value", 0))
            )
            score = _clamp(base + extras)
            
            # Enhanced score breakdown for v18.1
            f["score_breakdown"] = {
                "base": base,
                "extras": extras,
                "recency": rec,
                "source_trust": s_source,
                "keyword_score": s_keywords,
                "keyword_raw": s_keywords_raw,
                "weights": {
                    "w_source": w_source,
                    "w_keywords": w_keywords,
                    "w_recency": w_recency
                }
            }
            f["score"] = score
            f["scoring_version"] = cfg.scoring_version
            f["contributors"] = contributors[:10]  # Limit to top 10 contributors

        out.append(f)

    # Calculate final metrics
    end_time = time.time()
    metrics["processing_time_ms"] = (end_time - start_time) * 1000
    
    # Log metrics
    if metrics["source_trust_scores"]:
        avg_source_trust = sum(metrics["source_trust_scores"]) / len(metrics["source_trust_scores"])
        LOGGER.info(f"Source trust scores - avg: {avg_source_trust:.3f}, min: {min(metrics['source_trust_scores']):.3f}, max: {max(metrics['source_trust_scores']):.3f}")
    
    if metrics["keyword_scores"]:
        avg_keyword_score = sum(metrics["keyword_scores"]) / len(metrics["keyword_scores"])
        LOGGER.info(f"Keyword scores - avg: {avg_keyword_score:.3f}, min: {min(metrics['keyword_scores']):.3f}, max: {max(metrics['keyword_scores']):.3f}")
    
    LOGGER.info(f"Successfully scored {len(out)} findings with {cfg.scoring_version} in {metrics['processing_time_ms']:.1f}ms")
    
    # Add metrics to first finding for observability
    if out:
        out[0]["_scoring_metrics"] = metrics
    
    return out
