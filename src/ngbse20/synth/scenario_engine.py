import json
from typing import Any, Literal

from ..llm_client import LLMClient

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
    provider_priority: list[str] | None = None,
) -> dict[str, dict[str, Any]]:
    groups = group_by_themes(findings)
    out: dict[str, dict[str, Any]] = {}
    client = (
        LLMClient(provider_priority or ["openai", "azure_openai", "anthropic"])
        if mode == "api"
        else None
    )
    
    for theme, items in groups.items():
        avg = sum(i.get("score", 0.0) for i in items) / max(1, len(items))
        prob = _estimate_probability(avg, len(items))
        summary = ""
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
                "instructions": "Maak een beknopte NL-samenvatting (2-3 zinnen), zonder geheimen."
            }
            if mode == "api" and client:
                system_prompt = (
                    "You are a Dutch security analyst. Write concise, factual risk summaries."
                )
                user_prompt = json.dumps(payload, ensure_ascii=False)
                summary = (
                    client.call(system_prompt, user_prompt, max_tokens=300, temperature=0.2)
                    or ""
                )
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
        }
    return out
