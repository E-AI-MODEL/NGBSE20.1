"""Simple scoring engine v18."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


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

DEFAULT = ScoringConfig()

def _recency_score(ts: datetime, half_life_days: int) -> float:
    now = datetime.now(timezone.utc)
    age_days = max(0.0, (now - ts).total_seconds() / 86400.0)
    return 0.5 ** (age_days / float(half_life_days))

def _clamp(x: float) -> float:
    return max(0.0, min(1.0, float(x)))

def _source_score(f: dict) -> float:
    try:
        return float(f.get("metrics", {}).get("source", 0))
    except Exception:
        return 0.0

def _keyword_score(f: dict) -> float:
    try:
        return float(f.get("metrics", {}).get("keywords", 0))
    except Exception:
        return 0.0

def compute_cai(traces: list, cfg: dict[str, Any] | None = None) -> float:
    if not traces:
        return 0.0
    w = {"trace": 0.4, "transparency": 0.3, "blindspot": 0.3}
    if isinstance(cfg, dict) and "cai_weights" in cfg:
        w.update(cfg["cai_weights"])
    trs, trp, blind = [], [], 0
    for e in traces:
        rub = (e.get('rubric') or {})
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

    return _clamp(
        w["trace"] * mean(trs)
        + w["transparency"] * mean(trp)
        + w["blindspot"] * blind_rate
    )

def _parse_ts(ts_raw):
    if ts_raw is None:
        return None
    if isinstance(ts_raw, datetime):
        return ts_raw
    if isinstance(ts_raw, str):
        try:
            return datetime.fromisoformat(ts_raw.replace('Z','+00:00'))
        except Exception:
            return None
    return None

def score_findings(
    findings: list[dict[str, Any]], cfg: ScoringConfig = DEFAULT
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for f in findings:
        m = dict(f.get("metrics", {}))
        ts_dt = _parse_ts(f.get("timestamp"))
        rec = _recency_score(ts_dt, cfg.half_life_days) if ts_dt else 0.0
        base = (
            cfg.weights.get("source", 0) * _clamp(_source_score(f))
            + cfg.weights.get("keywords", 0) * _clamp(_keyword_score(f))
            + cfg.weights.get("recency", 0) * _clamp(rec)
        )
        extras = (
            cfg.extras.get("novelty", 0) * _clamp(m.get("novelty", 0))
            + cfg.extras.get("symbolic_consistency", 0)
            * _clamp(m.get("symbolic_consistency", 0))
            - cfg.extras.get("contradiction_penalty", 0)
            * _clamp(m.get("contradiction_penalty", 0))
            + cfg.extras.get("abduction_value", 0) * _clamp(m.get("abduction_value", 0))
        )
        score = _clamp(base + extras)
        f["score_breakdown"] = {"base": base, "extras": extras, "recency": rec}
        f["score"] = score
        out.append(f)
    return out
