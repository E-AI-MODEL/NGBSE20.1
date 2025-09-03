from typing import Any

MIN_SCORE = 0.6


def _seed_row(query: str, seed_type: str, priority: float, reason: str) -> dict[str, Any]:
    priority = max(0.1, min(1.0, float(priority)))
    return {
        "id": "S-PROPOSED",
        "query": query,
        "type": seed_type,
        "priority": priority,
        "reason": reason,
    }


def propose_next_seeds(
    findings: list[dict[str, Any]],
    asset_scores: dict[str, dict[str, float]],
) -> list[dict[str, Any]]:
    proposals: list[dict[str, Any]] = []
    seen_queries = set()

    top_assets = sorted(
        asset_scores.items(),
        key=lambda kv: kv[1].get("avg_e_ai_star", 0.0),
        reverse=True,
    )[:5]
    for asset, score_data in top_assets:
        if not asset or "." not in asset:
            continue
        q = f"site:{asset}"
        if q in seen_queries:
            continue
        seen_queries.add(q)
        priority = score_data.get("avg_e_ai_star", 0.6)
        reason = f"High-risk asset detected with score {priority:.2f}"
        proposals.append(_seed_row(q, "web", priority, reason))

    for f in findings[:20]:
        if f.get("score", 0.0) < MIN_SCORE:
            continue
        src = f.get("source", {})
        st = (src.get("type") or "").lower()
        asset = (f.get("asset") or "").lower()
        if st in {"github", "code"} and asset:
            q = f'site:github.com "{asset}" token'
            if q not in seen_queries:
                seen_queries.add(q)
                proposals.append(_seed_row(q, "code", 0.65, f"Follow-up on code finding for asset {asset}"))
        elif st in {"infra", "leak"} and asset:
            q = f'"{asset}" port:1883 MQTT'
            if q not in seen_queries:
                seen_queries.add(q)
                proposals.append(_seed_row(q, "infra", 0.6, f"Follow-up on infra finding for asset {asset}"))
    return proposals
