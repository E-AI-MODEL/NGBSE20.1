import os
import json
import glob
from typing import Dict, List, Any

def ewma(values: List[float], alpha: float=0.4) -> float:
    if not values: return 0.0
    s = values[0]
    for v in values[1:]:
        s = alpha * v + (1 - alpha) * s
    return s

def build_forecast(out_dir: str) -> Dict:
    history_glob = os.path.join(out_dir, "history", "*.asset_scores.json")
    os.makedirs(os.path.join(out_dir, "history"), exist_ok=True)
    series: Dict[str, List[float]] = {}
    for path in sorted(glob.glob(history_glob)):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for asset, vals in data.items():
                series.setdefault(asset, []).append(vals.get("avg_e_ai_star", 0.0))
        except Exception:
            continue
    forecast: Dict[str, Dict[str, float]] = {}
    for asset, seq in series.items():
        if not seq: continue
        ewma_val = ewma(seq, alpha=0.5)
        forecast[asset] = {
            "last_score": seq[-1],
            "trend_ewma": ewma_val,
            "projected_next": ewma_val
        }
    return forecast

def aggregate_asset_scores(findings: List[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
    by_asset: Dict[str, Dict[str, Any]] = {}
    for f in findings:
        asset = f.get("asset", "")
        if not asset: continue
        s = f.get("score", 0.0)
        if asset not in by_asset:
            by_asset[asset] = {"sum": 0.0, "n": 0}
        by_asset[asset]["sum"] += s
        by_asset[asset]["n"] += 1
    aggregated = {}
    for a, data in by_asset.items():
        avg = data["sum"] / max(1, data["n"])
        aggregated[a] = {"avg_e_ai_star": avg, "finding_count": data["n"]}
    return aggregated
