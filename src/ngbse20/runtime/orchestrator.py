"""
Pipeline orchestrator for NGBSE 20.3 (GA Version).
Modularized orchestrator with separated concerns and improved testability.
Order: validate -> collect -> score -> history -> forecast -> propose -> blindspots
-> BALLM -> scenarios -> export.
"""

from typing import Any, Optional
from pathlib import Path

from ..config.loader import ConfigLoader
from ..logging import get_logger
from .collector_manager import CollectorManager
from .pipeline_stages import PipelineStages
from ..export.export_manager import ExportManager

LOGGER = get_logger(__name__)


class PipelineOrchestrator:
    """Main pipeline orchestrator for NGBSE 20.3."""

    def __init__(self, config_dir: str = "config"):
        self.config_loader = ConfigLoader(config_dir)
        self.config = self.config_loader.load_config()
        self.credentials = self.config_loader.get_credentials()
        self.collector_manager = CollectorManager(self.config.model_dump(), self.credentials)
        self.pipeline_stages = PipelineStages(self.config.output_dir, self.config.model_dump())
        self.export_manager = ExportManager(self.config.model_dump())

    def run_pipeline(
        self,
        seeds: Optional[list[dict[str, Any]]] = None,
        rules: Optional[list[dict[str, Any]]] = None,
        metrics: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Run the complete NGBSE pipeline."""
        # Load configuration if not provided
        if seeds is None:
            seeds = self.config_loader.load_seeds()
        if rules is None:
            rules = self.config_loader.load_rules()

        metrics = metrics or {}
        traces: list[dict[str, Any]] = []
        allowlist = self.config.allowlist

        LOGGER.info(f"Starting pipeline with {len(seeds)} seeds and {len(rules)} rules")

        # 1. Validation Stage
        validation_result = self.pipeline_stages.validate_stage(rules, metrics)
        if validation_result["status"] == "blocked":
            return {"status": "blocked", "traces": [validation_result["trace"]]}

        # 2. Collection Stage
        collectors = self.collector_manager.build_collectors(allowlist)
        collection_result = self.pipeline_stages.collect_stage(seeds, collectors)
        findings = collection_result["findings"]
        traces.append(collection_result["trace"])

        # 3. Rules Stage
        rules_result = self.pipeline_stages.rules_stage(rules, metrics, findings)
        traces.append(rules_result["trace"])

        # 4. Scoring Stage
        scoring_result = self.pipeline_stages.scoring_stage(findings)
        scored_findings = scoring_result["scored_findings"]
        traces.append(scoring_result["trace"])

        # 5. Forecast Stage
        forecast_result = self.pipeline_stages.forecast_stage(scored_findings)
        asset_scores = forecast_result["asset_scores"]
        forecast = forecast_result["forecast"]
        history_path = forecast_result["history_path"]
        traces.append(forecast_result["trace"])

        # 6. Seed Proposal Stage
        seed_proposal_result = self.pipeline_stages.seed_proposal_stage(scored_findings, asset_scores)
        next_seeds = seed_proposal_result["next_seeds"]
        traces.append(seed_proposal_result["trace"])

        # 7. Blindspot Analysis Stage
        blindspot_result = self.pipeline_stages.blindspot_analysis_stage(scored_findings)
        blindspots = blindspot_result["blindspots"]
        traces.append(blindspot_result["trace"])

        # 8. BALLM Stage
        ballm_result = self.pipeline_stages.ballm_stage(scored_findings, blindspots, asset_scores)
        meta_layer = ballm_result["meta_layer"]
        traces.append(ballm_result["trace"])

        # 9. Scenario Stage
        scenario_result = self.pipeline_stages.scenario_stage(scored_findings)
        scenarios = scenario_result["scenarios"]
        traces.append(scenario_result["trace"])

        # 10. Brief Stage
        brief_result = self.pipeline_stages.brief_stage(scored_findings, asset_scores)
        brief = brief_result["brief"]

        # 11. Export Stage
        export_result = self.pipeline_stages.export_stage(scored_findings, traces)
        cai = export_result["cai"]
        bundle = export_result["bundle"]
        output_files = export_result["output_files"]
        traces.append(export_result["trace"])

        # 12. Modular Export Stage
        modular_export_result = self._run_modular_export_stage(
            scored_findings=scored_findings,
            brief=brief,
            blindspots=blindspots,
            forecast=forecast,
            scenarios=scenarios,
            ballm_meta_layer=meta_layer,
            bundle=bundle,
            next_seeds=next_seeds,
            traces=traces,
        )
        traces.append(modular_export_result["trace"])

        # 13. Report Stage (DOCX) - Legacy
        report_result = self.pipeline_stages.report_stage(
            brief=brief,
            blindspots=blindspots,
            forecast=forecast,
            scenarios=scenarios,
            ballm_meta_layer=meta_layer,
            bundle=bundle,
            next_seeds=next_seeds,
        )
        traces.append(report_result["trace"])

        LOGGER.info(f"Pipeline completed successfully with {len(scored_findings)} findings")

        return {
            "status": "ok",
            "cai": cai,
            "counts": {
                "findings": len(scored_findings),
                "forecasts": len(forecast),
                "next_seeds": len(next_seeds),
                "scenarios": len(scenarios),
            },
            "output_files": {
                "findings": output_files["findings"],
                "stix_bundle": output_files["stix_bundle"],
                "history": history_path,
            },
            "report_path": report_result.get("report_path"),
            "findings": scored_findings,
            "stix": bundle.serialize() if hasattr(bundle, "serialize") else bundle,
            "traces": traces,
            "forecast": forecast,
            "next_seeds": next_seeds,
            "blindspots": blindspots,
            "ballm_meta_layer": meta_layer,
            "scenarios": scenarios,
            "brief": brief,
        }

    def _run_modular_export_stage(
        self,
        scored_findings: list[dict[str, Any]],
        brief: str,
        blindspots: list[dict[str, Any]],
        forecast: list[dict[str, Any]],
        scenarios: list[dict[str, Any]],
        ballm_meta_layer: dict[str, Any],
        bundle: Any,
        next_seeds: list[dict[str, Any]],
        traces: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Run modular export stage with multiple formats."""
        try:
            LOGGER.info("Starting modular export stage")

            # Prepare export data
            export_data = {
                "findings": scored_findings,
                "brief": brief,
                "blindspots": blindspots,
                "forecast": forecast,
                "scenarios": scenarios,
                "ballm_meta_layer": ballm_meta_layer,
                "bundle": bundle,
                "next_seeds": next_seeds,
                "traces": traces,
                "config": {
                    "target": getattr(self.config, "target", "Unknown"),
                    "collectors": self.collector_manager.list_available_collectors(),
                    "timestamp": traces[0].get("timestamp") if traces else None,
                },
            }

            # Get export configuration
            export_config = getattr(self.config, "export", {})
            if isinstance(export_config, dict):
                formats = export_config.get("formats", ["csv", "html", "docx"])
                output_dir = Path(export_config.get("output_dir", self.config.output_dir))
            else:
                formats = ["csv", "html", "docx"]
                output_dir = Path(self.config.output_dir)

            # Create output directory
            output_dir.mkdir(parents=True, exist_ok=True)

            # Export in multiple formats
            export_results = self.export_manager.export_multiple(
                data=export_data, output_dir=output_dir, formats=formats
            )

            # Generate output files info
            output_files = {}
            for format, success in export_results.items():
                if success:
                    base_name = export_data["config"]["target"]
                    output_files[format] = str(output_dir / f"{base_name}.{format}")
                else:
                    LOGGER.warning(f"Export failed for format: {format}")

            # Create trace
            trace = {
                "stage": "modular_export",
                "status": "completed",
                "timestamp": traces[0].get("timestamp") if traces else None,
                "formats_exported": [f for f, s in export_results.items() if s],
                "formats_failed": [f for f, s in export_results.items() if not s],
                "output_files": output_files,
            }

            LOGGER.info(
                f"Modular export completed: {len([f for f, s in export_results.items() if s])} formats exported"
            )

            return {
                "status": "completed",
                "output_files": output_files,
                "export_results": export_results,
                "trace": trace,
            }

        except Exception as e:
            LOGGER.error(f"Modular export stage failed: {e}")
            trace = {
                "stage": "modular_export",
                "status": "failed",
                "error": str(e),
                "timestamp": traces[0].get("timestamp") if traces else None,
            }
            return {"status": "failed", "error": str(e), "trace": trace}

    def export_data(self, data: dict[str, Any], output_path: Path, format: str) -> bool:
        """Export data using the specified format."""
        return self.export_manager.export(data, output_path, format)

    def get_available_export_formats(self) -> list[str]:
        """Get list of available export formats."""
        return self.export_manager.get_available_formats()

    def get_export_summary(self, data: dict[str, Any]) -> dict[str, Any]:
        """Get export summary for data."""
        return self.export_manager.get_export_summary(data)


# Backward compatibility function
def run_pipeline(
    seeds: list[dict[str, Any]],
    rules: list[dict[str, Any]],
    metrics: Optional[dict[str, Any]] = None,
    config: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Backward compatibility function for the old API."""
    orchestrator = PipelineOrchestrator()
    if config:
        # Update config attributes if provided
        for key, value in config.items():
            if hasattr(orchestrator.config, key):
                setattr(orchestrator.config, key, value)
    return orchestrator.run_pipeline(seeds, rules, metrics)
