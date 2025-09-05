from __future__ import annotations

import json
from typing import Any, Literal

from ..llm_factory import build_llm
from ..config.models import LLMConfig, ProfileConfig
from ..utils.validation import validate_llm_output, SCENARIO_SCHEMA
from ..utils.prompt_hash import hash_prompt

HIGH_RISK_THRESHOLD = 0.75


def _estimate_probability(avg_score: float, evidence_count: int, prior: float = 0.10) -> float:
    lr = 1 + 9 * max(0.0, (avg_score - 0.5) / 0.5)
    odds = (prior / (1 - prior)) * lr * max(1.0, min(5.0, evidence_count / 3.0))
    return odds / (1 + odds)


def group_by_themes(findings: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    themes = {
        "Public_Code_Exposure": ["github", "oidc", "token", "secret"],
        "Exposed_Cloud_Signed_URLs": [
            "sv=",
            "signature=",
            "blob.core.windows.net",
            "x-amz-signature",
            "x-goog-signature",
        ],
        "Exposed_IoT_Infrastructure": ["mqtt", "port:1883", "anonymous"],
        "Archive_Only_Findings": ["web.archive.org", "wayback"],
    }
    grouped: dict[str, list[dict[str, Any]]] = {k: [] for k in themes}
    for f in findings:
        text = (f.get("source", {}).get("url", "") + " " + f.get("asset", "")).lower()
        assigned = False
        for theme, kws in themes.items():
            if any(k in text for k in kws):
                grouped[theme].append(f)
                assigned = True
                break
        if not assigned and f.get("score", 0.0) >= HIGH_RISK_THRESHOLD:
            grouped.setdefault("High_Risk_Generic", []).append(f)
    return {k: v for k, v in grouped.items() if v}


def build_scenarios(
    findings: list[dict[str, Any]],
    mode: Literal["none", "prompt", "api"] = "none",
    llm_config: LLMConfig = None,
    profile: ProfileConfig = None,
) -> dict[str, dict[str, Any]]:
    groups = group_by_themes(findings)
    out: dict[str, dict[str, Any]] = {}
    llm_handle = None
    
    if mode == "api" and llm_config:
        llm_handle = build_llm(llm_config, profile)

    for theme, items in groups.items():
        avg = sum(i.get("score", 0.0) for i in items) / max(1, len(items))
        prob = _estimate_probability(avg, len(items))
        summary = ""
        # Derive additional template fields for non-LLM mode
        risk_level = "High" if avg > 0.7 else ("Medium" if avg > 0.4 else "Low")
        mitigation_priority = "Immediate" if avg > 0.7 else ("Short-term" if avg > 0.4 else "Planned")
        if mode == "none":
            summary = (
                f"Theme '{theme.replace('_', ' ')}' requires manual review. "
                f"Found {len(items)} findings with average score {avg:.2f}."
            )
        if mode in ("prompt", "api"):
            payload = {
                "theme": theme,
                "avg_score": round(avg, 3),
                "evidence_count": len(items),
                "examples": [
                    {
                        "asset": it.get("asset"),
                        "url": it.get("source", {}).get("url"),
                        "type": it.get("source", {}).get("type"),
                    }
                    for it in items[:8]
                ],
                "instructions": ("Make a concise summary (2-3 sentences), without secrets."),
            }
            if mode == "api" and llm_handle:
                system_prompt = "You are a security analyst. Write concise, factual risk summaries."
                user_prompt = json.dumps(payload, ensure_ascii=False)
                
                # Generate hash for audit trail
                prompt_hash = hash_prompt(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    model=llm_handle.model,
                    params=llm_handle.params,
                    seed=llm_config.seed if llm_config else None
                )
                
                try:
                    raw_response = llm_handle.generate(system_prompt, user_prompt)
                    
                    # Try to parse as structured JSON first
                    try:
                        validated_response = validate_llm_output(raw_response, SCENARIO_SCHEMA)
                        summary = validated_response.get("summary", raw_response)
                    except (json.JSONDecodeError, Exception):
                        summary = raw_response or ""
                except Exception:
                    summary = ""
            else:
                try:
                    with open("out/prompt.scenarios.json", "w", encoding="utf-8") as h:
                        json.dump(payload, h, ensure_ascii=False, indent=2)
                except Exception:
                    pass
        out[theme] = {
            "future_scenario": theme.replace("_", " "),
            "probability_90_days": prob,
            "semantic_summary": summary,
            "avg_eai_score": round(avg, 3),
            "evidence_count": len(items),
            "risk_level": risk_level,
            "mitigation_priority": mitigation_priority,
        }
    return out
