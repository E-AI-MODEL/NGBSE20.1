"""
Pipeline stages for NGBSE 20.2.
Separates pipeline logic into distinct, testable stages.
"""

import json
import os
from datetime import UTC, datetime
from typing import Any

from ..ballm.meta_layer_generator import BALLMMetaLayerGenerator
from ..export.stix import to_stix_bundle
from ..forecast.engine import aggregate_asset_scores, build_forecast
from ..llm_client import LLMClient
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

LOGGER = get_logger(__name__)


class PipelineStages:
    """Manages individual pipeline stages."""

    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def validate_stage(
        self, rules: list[dict[str, Any]], metrics: dict[str, Any]
    ) -> dict[str, Any]:
        """Validation stage - check for hard blocks."""
        acts_block = evaluate_rules(
            [r for r in rules if r.get("action", {}).get("type") == "hard_block"],
            metrics,
        )

        if acts_block:
            trace = event(
                "validate",
                {"metrics": metrics},
                {"hard_block": True},
                "hard block triggered",
                rules_fired=[a["rule_id"] for a in acts_block],
            )
            return {"status": "blocked", "trace": trace}

        return {"status": "ok"}

    def collect_stage(
        self, seeds: list[dict[str, Any]], collectors: list[Any]
    ) -> dict[str, Any]:
        """Collection stage - gather findings from all collectors."""
        findings = []
        timestamp = datetime.now(UTC).isoformat()

        for seed in seeds:
            seed_findings = []
            for collector in collectors:
                try:
                    collector_findings = collector.collect(seed, timestamp)
                    seed_findings.extend(collector_findings)
                    LOGGER.debug(
                        f"Collector {collector.__class__.__name__} found {len(collector_findings)} items for seed {seed.get('id')}"
                    )
                except Exception as e:
                    LOGGER.error(
                        f"Collector {collector.__class__.__name__} failed for seed {seed.get('id')}: {e}"
                    )

            findings.extend(seed_findings)

        trace = event(
            "collect",
            {"n_seeds": len(seeds), "n_collectors": len(collectors)},
            {"n_findings": len(findings)},
            "collected findings",
        )

        return {"findings": findings, "trace": trace}

    def rules_stage(
        self,
        rules: list[dict[str, Any]],
        metrics: dict[str, Any],
        findings: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Rules evaluation stage - apply non-blocking rules."""
        acts_warn = evaluate_rules(
            [r for r in rules if r.get("action", {}).get("type") != "hard_block"],
            metrics,
        )

        # Apply warning flags to findings
        for a in acts_warn:
            if a.get("type") == "warning_flag" and findings:
                for f in findings:
                    f.setdefault("provenance", {}).setdefault("actions", []).append(a)

        trace = event(
            "rules",
            {"metrics": metrics},
            {"actions": acts_warn},
            "rules evaluated",
            rules_fired=[a.get("rule_id") for a in acts_warn],
        )

        return {"actions": acts_warn, "trace": trace}

    def scoring_stage(self, findings: list[dict[str, Any]]) -> dict[str, Any]:
        """Scoring stage - score all findings."""
        scored_findings = score_findings(findings, SCORE_DEFAULT)

        trace = event(
            "scoring",
            {"n_in": len(findings)},
            {"n_out": len(scored_findings)},
            "scored findings",
        )

        return {"scored_findings": scored_findings, "trace": trace}

    def forecast_stage(self, scored_findings: list[dict[str, Any]]) -> dict[str, Any]:
        """Forecast stage - generate asset scores and forecasts."""
        try:
            asset_scores = aggregate_asset_scores(scored_findings)

            # Save history
            history_dir = os.path.join(self.output_dir, "history")
            os.makedirs(history_dir, exist_ok=True)
            ts_filename = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
            history_path = os.path.join(history_dir, f"{ts_filename}.asset_scores.json")

            with open(history_path, "w", encoding="utf-8") as f:
                json.dump(asset_scores, f, indent=2)

            forecast = build_forecast(self.output_dir)

            trace = event(
                "forecast",
                {"n_assets": len(asset_scores)},
                {"n_forecasts": len(forecast)},
                "generated forecast",
            )

            return {
                "asset_scores": asset_scores,
                "forecast": forecast,
                "history_path": history_path,
                "trace": trace,
            }

        except Exception as e:
            LOGGER.error(f"Forecast stage failed: {e}")
            # Return empty forecast on failure
            default_forecast = []
            default_asset_scores = {}

            trace = event(
                "forecast",
                {"n_assets": 0},
                {"n_forecasts": 0, "error": str(e)},
                "forecast generation failed",
            )

            return {
                "asset_scores": default_asset_scores,
                "forecast": default_forecast,
                "history_path": None,
                "trace": trace,
            }

    def seed_proposal_stage(
        self, scored_findings: list[dict[str, Any]], asset_scores: dict[str, Any]
    ) -> dict[str, Any]:
        """Seed proposal stage - propose new seeds."""
        next_seeds = propose_next_seeds(scored_findings, asset_scores)

        trace = event(
            "seed_proposal",
            {"n_findings": len(scored_findings)},
            {"n_new_seeds": len(next_seeds)},
            "proposed new seeds",
        )

        return {"next_seeds": next_seeds, "trace": trace}

    def blindspot_analysis_stage(
        self, scored_findings: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Blindspot analysis stage - identify coverage gaps."""
        try:
            blindspots = {
                "coverage": coverage_gap(scored_findings),
                "recency": recency_gap(scored_findings),
                "confidence": confidence_gap(scored_findings),
            }

            trace = event(
                "blindspot_analysis",
                {},
                {"gaps_identified": len(blindspots)},
                "analyzed blind spots",
            )

            return {"blindspots": blindspots, "trace": trace}

        except Exception as e:
            LOGGER.error(f"Blindspot analysis failed: {e}")
            # Return default blindspots on failure
            default_blindspots = {
                "coverage": {"score": 0.0, "description": "Analysis failed"},
                "recency": {"score": 0.0, "description": "Analysis failed"},
                "confidence": {"score": 0.0, "description": "Analysis failed"},
            }

            trace = event(
                "blindspot_analysis",
                {},
                {"gaps_identified": 0, "error": str(e)},
                "blindspot analysis failed",
            )

            return {"blindspots": default_blindspots, "trace": trace}

    def ballm_stage(
        self,
        scored_findings: list[dict[str, Any]],
        blindspots: dict[str, Any],
        asset_scores: dict[str, Any],
    ) -> dict[str, Any]:
        """BALLM meta-layer generation stage."""
        try:
            ballm_generator = BALLMMetaLayerGenerator(LLMClient())
            meta_layer = ballm_generator.generate_meta_layer(
                scored_findings, blindspots, asset_scores
            )

            trace = event(
                "ballm_meta_layer",
                {},
                {
                    "meta_layer_generated": True,
                    "epistemic_humility": meta_layer.get(
                        "epistemic_humility_score", 0.0
                    ),
                },
                "generated BALLM meta-layer with epistemic insights",
            )

            return {"meta_layer": meta_layer, "trace": trace}

        except Exception as e:
            LOGGER.warning(f"BALLM meta-layer generation failed: {e}")
            meta_layer = {"error": str(e)}

            trace = event(
                "ballm_meta_layer",
                {},
                {"meta_layer_generated": False, "error": str(e)},
                "BALLM meta-layer generation failed",
            )

            return {"meta_layer": meta_layer, "trace": trace}

    def scenario_stage(self, scored_findings: list[dict[str, Any]]) -> dict[str, Any]:
        """Scenario synthesis stage."""
        scenarios = build_scenarios(
            scored_findings, mode=os.getenv("NGBSE_SCENARIO_MODE", "none")
        )

        trace = event(
            "scenario_synthesis",
            {},
            {"scenarios": len(scenarios)},
            "synthesized scenarios",
        )

        return {"scenarios": scenarios, "trace": trace}

    def brief_stage(
        self, scored_findings: list[dict[str, Any]], asset_scores: dict[str, Any]
    ) -> dict[str, Any]:
        """Brief synthesis stage."""
        brief = synthesize_brief_llm(
            scored_findings,
            asset_scores,
            mode=os.getenv("NGBSE_BRIEF_MODE", "none"),
            out_dir=self.output_dir,
        )

        return {"brief": brief}

    def export_stage(
        self, scored_findings: list[dict[str, Any]], traces: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Export stage - generate STIX bundle and save outputs."""
        cai = compute_cai(traces, {})
        bundle = to_stix_bundle(scored_findings)

        # Save findings
        findings_path = os.path.join(self.output_dir, "findings.json")
        with open(findings_path, "w", encoding="utf-8") as f:
            json.dump(scored_findings, f, indent=2, ensure_ascii=False)

        # Save STIX bundle
        stix_path = os.path.join(self.output_dir, "stix_bundle.json")
        with open(stix_path, "w", encoding="utf-8") as f:
            json.dump(json.loads(bundle.serialize()), f, indent=2, ensure_ascii=False)

        trace = event(
            "export",
            {"n": len(scored_findings)},
            {"bundle_objects": len(bundle.objects)},
            "exported STIX",
        )

        return {
            "cai": cai,
            "bundle": bundle,
            "output_files": {"findings": findings_path, "stix_bundle": stix_path},
            "trace": trace,
        }
