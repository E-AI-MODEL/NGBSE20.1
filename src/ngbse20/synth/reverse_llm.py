import json
import os
from collections import Counter
from typing import Any

from ..llm_client import LLMClient


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
        asset_scores.items(), key=lambda kv: kv[1].get("avg_e_ai_star", 0.0), reverse=True
    )[:5]
    bluf = "Key findings consolidated. See risks and actions per asset."
    risks = [{"asset": a, "risk": round(v["avg_e_ai_star"], 3)} for a, v in top_assets]
    actions = [
        "Validate top assets manually (sign-off required)",
        "Check coverage imbalance and fill missing source classes",
        "Plan new run within 7 days for trend monitoring"
    ]
    return {"BLUF": bluf, "TopRisks": risks, "Actions": actions}

def synthesize_brief_llm(
    findings: list[dict[str, Any]],
    asset_scores: dict[str, dict[str, float]],
    mode: str = "none",
    provider_priority: list[str] | None = None,
    out_dir: str | None = None,
) -> dict[str, Any]:
    base = synthesize_brief(findings, asset_scores)
    mode = (mode or "none").lower()
    if mode == "none":
        return base

    top_assets = sorted(asset_scores.items(), key=lambda kv: kv[1].get("avg_e_ai_star", 0.0), reverse=True)[:5]
    payload = {
        "instruction": "Write a concise BLUF (2-3 sentences) + 3 actions. Be factual, no secrets.",
        "top_assets": [{"asset": a, "avg_eai": round(v["avg_e_ai_star"],3)} for a, v in top_assets],
        "examples": [
            {
                "asset": f.get("asset"),
                "type": f.get("source",{}).get("type"),
                "url": f.get("source",{}).get("url"),
                "score": f.get("score", 0.0)
            }
            for f in findings[:10]
        ]
    }
    if mode == "prompt":
        try:
            if out_dir:
                with open(
                    os.path.join(out_dir, "prompt.brief.json"), "w", encoding="utf-8"
                ) as h:
                    json.dump(payload, h, ensure_ascii=False, indent=2)
        except Exception:
            pass
        return base

    if mode == "api":
        client = LLMClient(provider_priority or ["openai", "azure_openai", "anthropic"])
        system_prompt = "You are a Dutch security analyst. Produce concise BLUF and 3 concrete actions."
        user_prompt = json.dumps(payload, ensure_ascii=False)
        txt = client.call(system_prompt, user_prompt, max_tokens=400, temperature=0.2)
        if isinstance(txt, str) and txt.strip():
            return {**base, "BLUF": txt.strip()}
    return base
HIGH_SCORE_THRESHOLD = 0.7
LOW_QUALITY_THRESHOLD = 0.5
