"""Pipeline orchestrator for NGBSE 20.1.
Order: validate -> collect -> score -> history -> forecast -> propose -> export.
"""
import json
import os
from datetime import datetime, timezone
from typing import Dict, Any, List

from ..rules.engine import evaluate_rules
from ..scoring.v18 import score_findings, DEFAULT as SCORE_DEFAULT, compute_cai
from ..trace.logger import event
from ..export.stix import to_stix
from ..collectors.http_web import HttpWebCollector
from ..forecast.engine import build_forecast, aggregate_asset_scores
from ..seeds.proposer import propose_next_seeds


def run_pipeline(
    seeds: List[Dict[str, Any]],
    rules: List[Dict[str, Any]],
    metrics: Dict[str, Any] | None = None,
    config: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    config = config or {"output_dir": "out", "allowlist": ["*"]}
    output_dir = config.get("output_dir", "out")
    allowlist = config.get("allowlist", ["*"])

    traces: List[Dict[str, Any]] = []
    metrics = metrics or {}
    now_iso = datetime.now(timezone.utc).isoformat()

    acts_block = evaluate_rules([r for r in rules if r.get("action", {}).get("type") == "hard_block"], metrics)
    if acts_block:
        traces.append(event("validate", {"metrics": metrics}, {"hard_block": True}, "hard block triggered", rules_fired=[a['rule_id'] for a in acts_block]))
        return {"status": "blocked", "traces": traces}

    collector = HttpWebCollector(allowlist_domains=allowlist)
    findings: List[Dict[str, Any]] = []
    for seed in seeds:
        try:
            findings.extend(collector.collect(seed, now_iso))
        except Exception as e:
            print(f"Collector error for seed {seed.get('id')}: {e}")
    traces.append(event("collect", {"n_seeds": len(seeds)}, {"n_findings": len(findings)}, "collected findings"))

    acts_warn = evaluate_rules([r for r in rules if r.get("action", {}).get("type") != "hard_block"], metrics)
    traces.append(event("rules", {"metrics": metrics}, {"actions": acts_warn}, "rules evaluated", rules_fired=[a.get('rule_id') for a in acts_warn]))
    for a in acts_warn:
        if a.get("type") == "warning_flag" and findings:
            for f in findings:
                f.setdefault("provenance", {}).setdefault("actions", []).append(a)

    scored_findings = score_findings(findings, SCORE_DEFAULT)
    traces.append(event("scoring", {"n_in": len(findings)}, {"n_out": len(scored_findings)}, "scored findings"))

    asset_scores = aggregate_asset_scores(scored_findings)
    history_dir = os.path.join(output_dir, "history")
    os.makedirs(history_dir, exist_ok=True)
    ts_filename = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    history_path = os.path.join(history_dir, f"{ts_filename}.asset_scores.json")
    with open(history_path, "w", encoding="utf-8") as f:
        json.dump(asset_scores, f, indent=2)

    forecast = build_forecast(output_dir)
    traces.append(event("forecast", {"n_assets": len(asset_scores)}, {"n_forecasts": len(forecast)}, "generated forecast"))

    next_seeds = propose_next_seeds(scored_findings, asset_scores)
    traces.append(event("seed_proposal", {"n_findings": len(scored_findings)}, {"n_new_seeds": len(next_seeds)}, "proposed new seeds"))

    cai = compute_cai(traces, {})
    bundle = to_stix(scored_findings, traces)
    traces.append(event("export", {"n": len(scored_findings)}, {"bundle_objects": len(bundle.get("objects", []))}, "exported STIX"))

    return {
        "status": "ok",
        "findings": scored_findings,
        "stix": bundle,
        "traces": traces,
        "cai": cai,
        "forecast": forecast,
        "next_seeds": next_seeds,
    }
