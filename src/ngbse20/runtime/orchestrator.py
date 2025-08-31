"""
Pipeline orchestrator for NGBSE 20.1 (Complete Version).
Order: validate -> collect -> score -> history -> forecast -> propose -> blindspots -> BALLM -> scenarios -> export.
"""
import json
import os
from datetime import datetime, timezone
from typing import Any

from ..collectors.http_web import HttpWebCollector
from ..export.stix import to_stix_bundle
from ..forecast.engine import aggregate_asset_scores, build_forecast
from ..logging import get_logger
from ..rules.engine import evaluate_rules
from ..scoring.v18 import DEFAULT as SCORE_DEFAULT, compute_cai, score_findings
from ..seeds.proposer import propose_next_seeds
from ..synth.reverse_llm import (
    confidence_gap,
    coverage_gap,
    recency_gap,
    synthesize_brief_llm,
)
from ..synth.scenario_engine import build_scenarios
from ..trace.logger import event
from ..ballm.meta_layer_generator import BALLMMetaLayerGenerator
from ..llm_client import LLMClient

LOGGER = get_logger(__name__)


def run_pipeline(
    seeds: list[dict[str, Any]],
    rules: list[dict[str, Any]],
    metrics: dict[str, Any] | None = None,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    config = config or {"output_dir": "out", "allowlist": ["*"]}
    output_dir = config.get("output_dir", "out")
    allowlist = config.get("allowlist", ["*"])
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    traces: list[dict[str, Any]] = []
    metrics = metrics or {}
    now_iso = datetime.now(timezone.utc).isoformat()

    # 1. Validation Gate
    acts_block = evaluate_rules(
        [r for r in rules if r.get("action", {}).get("type") == "hard_block"], metrics
    )
    if acts_block:
        traces.append(
            event(
                "validate",
                {"metrics": metrics},
                {"hard_block": True},
                "hard block triggered",
                rules_fired=[a["rule_id"] for a in acts_block],
            )
        )
        return {"status": "blocked", "traces": traces}

    # 2. Collection
    collector = HttpWebCollector(allowlist_domains=allowlist)
    findings: list[dict[str, Any]] = []
    for seed in seeds:
        try:
            findings.extend(collector.collect(seed, now_iso))
        except Exception as e:
            LOGGER.error(f"Collector error for seed {seed.get('id')}: {e}")
    traces.append(
        event("collect", {"n_seeds": len(seeds)}, {"n_findings": len(findings)}, "collected findings")
    )

    # 3. Rules (non-blocking)
    acts_warn = evaluate_rules(
        [r for r in rules if r.get("action", {}).get("type") != "hard_block"], metrics
    )
    traces.append(
        event(
            "rules",
            {"metrics": metrics},
            {"actions": acts_warn},
            "rules evaluated",
            rules_fired=[a.get("rule_id") for a in acts_warn],
        )
    )
    for a in acts_warn:
        if a.get("type") == "warning_flag" and findings:
            for f in findings:
                f.setdefault("provenance", {}).setdefault("actions", []).append(a)

    # 4. Scoring
    scored_findings = score_findings(findings, SCORE_DEFAULT)
    traces.append(
        event(
            "scoring",
            {"n_in": len(findings)},
            {"n_out": len(scored_findings)},
            "scored findings",
        )
    )

    # 5. History & Forecast
    asset_scores = aggregate_asset_scores(scored_findings)
    history_dir = os.path.join(output_dir, "history")
    os.makedirs(history_dir, exist_ok=True)
    ts_filename = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    history_path = os.path.join(history_dir, f"{ts_filename}.asset_scores.json")
    with open(history_path, "w", encoding="utf-8") as f:
        json.dump(asset_scores, f, indent=2)

    forecast = build_forecast(output_dir)
    traces.append(
        event(
            "forecast",
            {"n_assets": len(asset_scores)},
            {"n_forecasts": len(forecast)},
            "generated forecast",
        )
    )

    # 6. Seed Proposal
    next_seeds = propose_next_seeds(scored_findings, asset_scores)
    traces.append(
        event(
            "seed_proposal",
            {"n_findings": len(scored_findings)},
            {"n_new_seeds": len(next_seeds)},
            "proposed new seeds",
        )
    )
    
    # 7. Blindspot Analysis
    blindspots = {
        "coverage": coverage_gap(scored_findings),
        "recency": recency_gap(scored_findings),
        "confidence": confidence_gap(scored_findings)
    }
    traces.append(
        event(
            "blindspot_analysis",
            {},
            {"gaps_identified": len(blindspots)},
            "analyzed blind spots",
        )
    )
    
    # 7.5. BALLM Meta-Layer Generation
    try:
        ballm_generator = BALLMMetaLayerGenerator(LLMClient())
        meta_layer = ballm_generator.generate_meta_layer(scored_findings, blindspots, asset_scores)
        traces.append(
            event(
                "ballm_meta_layer",
                {},
                {"meta_layer_generated": True, "epistemic_humility": meta_layer.get("epistemic_humility_score", 0.0)},
                "generated BALLM meta-layer with epistemic insights",
            )
        )
    except Exception as e:
        LOGGER.warning(f"BALLM meta-layer generation failed: {e}")
        meta_layer = {"error": str(e)}

    # 8. Scenario Synthesis (Optional LLM)
    scenarios = build_scenarios(scored_findings, mode=os.getenv("NGBSE_SCENARIO_MODE", "none"))
    traces.append(
        event(
            "scenario_synthesis",
            {},
            {"scenarios": len(scenarios)},
            "synthesized scenarios",
        )
    )

    # 9. Brief Synthesis (Optional LLM)
    brief = synthesize_brief_llm(scored_findings, asset_scores, mode=os.getenv("NGBSE_BRIEF_MODE", "none"), out_dir=output_dir)

    # 10. Final Export & Reporting
    cai = compute_cai(traces, {})
    bundle = to_stix_bundle(scored_findings)
    traces.append(
        event(
            "export",
            {"n": len(scored_findings)},
            {"bundle_objects": len(bundle.objects)},
            "exported STIX",
        )
    )

    # Save findings to output directory
    findings_path = os.path.join(output_dir, "findings.json")
    with open(findings_path, "w", encoding="utf-8") as f:
        json.dump(scored_findings, f, indent=2, ensure_ascii=False)

    # Save STIX bundle
    stix_path = os.path.join(output_dir, "stix_bundle.json")
    with open(stix_path, "w", encoding="utf-8") as f:
        json.dump(json.loads(bundle.serialize()), f, indent=2, ensure_ascii=False)

    return {
        "status": "ok",
        "cai": cai,
        "counts": {
            "findings": len(scored_findings),
            "forecasts": len(forecast),
            "next_seeds": len(next_seeds),
            "scenarios": len(scenarios)
        },
        "output_files": {
            "findings": findings_path,
            "stix_bundle": stix_path,
            "history": history_path
        },
        "findings": scored_findings,
        "stix": json.loads(bundle.serialize()),
        "traces": traces,
        "forecast": forecast,
        "next_seeds": next_seeds,
        "blindspots": blindspots,
        "ballm_meta_layer": meta_layer,
        "scenarios": scenarios,
        "brief": brief
    }
