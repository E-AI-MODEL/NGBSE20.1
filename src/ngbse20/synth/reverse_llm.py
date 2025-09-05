from __future__ import annotations

import json
import os
from collections import Counter
from typing import Any

from ..llm_factory import build_llm
from ..config.models import LLMConfig, ProfileConfig
from ..utils.validation import validate_llm_output, RISK_ANALYSIS_SCHEMA
from ..utils.prompt_hash import hash_prompt
from ..logging import get_logger

LOGGER = get_logger(__name__)


def coverage_gap(findings: list[dict[str, Any]]) -> dict[str, Any]:
    cats: list[str] = []
    for f in findings:
        t = f.get("source", {}).get("type", "")
        if t == "pdf":
            cats.append("Archive/PDF")
        elif t == "ti_post":
            cats.append("TI/Blog")
        elif t == "news":
            cats.append("News")
        else:
            cats.append("Web")
    c = Counter(cats)
    total = sum(c.values())
    if total == 0:
        return {"ratios": {}, "max_category": "", "imbalance": 0.0}
    ratios = {k: v / total for k, v in c.items()}
    max_cat = max(ratios, key=ratios.get) if ratios else ""
    imbalance = (max(ratios.values()) - min(ratios.values())) if len(ratios) > 1 else 0.0
    return {"ratios": ratios, "max_category": max_cat, "imbalance": imbalance}


def recency_gap(findings: list[dict[str, Any]]) -> dict[str, Any]:
    days = Counter(
        [
            (f.get("timestamps", {}).get("observed", "") or "")[:10]
            for f in findings
            if f.get("timestamps", {}).get("observed")
        ]
    )
    if not days:
        return {"spike": False, "detail": {}}
    peak_day, peak_count = max(days.items(), key=lambda kv: kv[1])
    spike = peak_count >= max(3, int(0.7 * sum(days.values())))
    return {"spike": spike, "detail": dict(days)}


def confidence_gap(findings: list[dict[str, Any]]) -> dict[str, Any]:
    high_score_assets: list[str] = []
    low_quality_assets: set[str] = set()
    for f in findings:
        e = f.get("score", 0.0)
        q = f.get("quality", {}).get("q", 0.0)
        if e >= HIGH_SCORE_THRESHOLD:
            high_score_assets.append(f.get("asset", ""))
        if q < LOW_QUALITY_THRESHOLD:
            low_quality_assets.add(f.get("asset", ""))
    risky = sorted({a for a in high_score_assets if a in low_quality_assets})
    return {"risky_assets": risky, "n": len(risky)}


def synthesize_brief(findings: list[dict[str, Any]], asset_scores: dict[str, dict[str, float]]) -> dict[str, Any]:
    top_assets = sorted(
        asset_scores.items(),
        key=lambda kv: kv[1].get("avg_e_ai_star", 0.0),
        reverse=True,
    )[:5]
    bluf = "Key findings consolidated. See risks and actions per asset."
    risks = [{"asset": a, "risk": round(v["avg_e_ai_star"], 3)} for a, v in top_assets]
    actions = [
        "Validate top assets manually (sign-off required)",
        "Check coverage imbalance and fill missing source classes",
        "Plan new run within 7 days for trend monitoring",
    ]
    return {"BLUF": bluf, "TopRisks": risks, "Actions": actions}


def synthesize_brief_llm(
    findings: list[dict[str, Any]],
    asset_scores: dict[str, dict[str, float]],
    mode: str = "none",
    llm_config: LLMConfig = None,
    profile: ProfileConfig = None,
    out_dir: str | None = None,
) -> dict[str, Any]:
    base = synthesize_brief(findings, asset_scores)
    mode = (mode or "none").lower()
    if mode == "none":
        return base

    top_assets = sorted(
        asset_scores.items(),
        key=lambda kv: kv[1].get("avg_e_ai_star", 0.0),
        reverse=True,
    )[:5]
    payload = {
        "instruction": ("Write a concise BLUF (2-3 sentences) + 3 actions. Be factual, no secrets."),
        "top_assets": [{"asset": a, "avg_eai": round(v["avg_e_ai_star"], 3)} for a, v in top_assets],
        "examples": [
            {
                "asset": f.get("asset"),
                "type": f.get("source", {}).get("type"),
                "url": f.get("source", {}).get("url"),
                "score": f.get("score", 0.0),
            }
            for f in findings[:10]
        ],
    }
    if mode == "prompt":
        try:
            if out_dir:
                with open(os.path.join(out_dir, "prompt.brief.json"), "w", encoding="utf-8") as h:
                    json.dump(payload, h, ensure_ascii=False, indent=2)
        except Exception:
            pass
        return base

    if mode == "api" and llm_config:
        llm_handle = build_llm(llm_config, profile)
        system_prompt = (
            "You are a senior cybersecurity threat intelligence analyst. "
            "Produce a concise BLUF (1-2 sentences), a list of top risks, and 3 actionable mitigation steps. "
            "Be factual and grounded in the provided evidence."
        )
        user_prompt = json.dumps(payload, ensure_ascii=False)
        
        # Generate hash for audit trail
        prompt_hash = hash_prompt(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model=llm_handle.model,
            params=llm_handle.params,
            seed=llm_config.seed
        )
        
        try:
            raw_response = llm_handle.generate(system_prompt, user_prompt)
            
            # Try to parse structured JSON first
            if isinstance(raw_response, str) and raw_response.strip():
                try:
                    validated_response = validate_llm_output(raw_response, RISK_ANALYSIS_SCHEMA)
                    return {
                        "BLUF": validated_response.get("BLUF", base["BLUF"]),
                        "TopRisks": validated_response.get("TopRisks", base["TopRisks"]),
                        "Actions": validated_response.get("Actions", base["Actions"]),
                        "prompt_hash": prompt_hash,
                        "model_info": {
                            "provider": llm_handle.provider,
                            "model": llm_handle.model,
                            "params": llm_handle.params
                        }
                    }
                except (json.JSONDecodeError, Exception):
                    # If model returned plain text instead of JSON, fall back to BLUF-only merge
                    LOGGER.warning("LLM returned non-conforming JSON. Falling back to base + BLUF text.")
                    return {**base, "BLUF": raw_response.strip()}
        except Exception as e:
            LOGGER.error(f"LLM call failed: {e}")
            return base

    # Ultimate fallback
    return base

HIGH_SCORE_THRESHOLD = 0.7
LOW_QUALITY_THRESHOLD = 0.5
