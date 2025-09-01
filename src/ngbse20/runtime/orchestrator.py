"""
Pipeline orchestrator for NGBSE 20.2 (GA Version).
Modularized orchestrator with separated concerns and improved testability.
Order: validate -> collect -> score -> history -> forecast -> propose -> blindspots -> BALLM -> scenarios -> export.
"""
from typing import Any, Dict, List

from ..config.loader import ConfigLoader
from ..logging import get_logger
from .collector_manager import CollectorManager
from .pipeline_stages import PipelineStages

LOGGER = get_logger(__name__)


class PipelineOrchestrator:
    """Main pipeline orchestrator for NGBSE 20.2."""
    
    def __init__(self, config_dir: str = "config"):
        self.config_loader = ConfigLoader(config_dir)
        self.config = self.config_loader.load_config()
        self.credentials = self.config_loader.get_credentials()
        self.collector_manager = CollectorManager(self.config.__dict__, self.credentials)
        self.pipeline_stages = PipelineStages(self.config.output_dir)


    def run_pipeline(
        self,
        seeds: List[Dict[str, Any]] = None,
        rules: List[Dict[str, Any]] = None,
        metrics: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """Run the complete NGBSE pipeline."""
        # Load configuration if not provided
        if seeds is None:
            seeds = self.config_loader.load_seeds()
        if rules is None:
            rules = self.config_loader.load_rules()
        
        metrics = metrics or {}
        traces: List[Dict[str, Any]] = []
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
        
        LOGGER.info(f"Pipeline completed successfully with {len(scored_findings)} findings")
        
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
                "findings": output_files["findings"],
                "stix_bundle": output_files["stix_bundle"],
                "history": history_path
            },
            "findings": scored_findings,
            "stix": bundle.serialize() if hasattr(bundle, 'serialize') else bundle,
            "traces": traces,
            "forecast": forecast,
            "next_seeds": next_seeds,
            "blindspots": blindspots,
            "ballm_meta_layer": meta_layer,
            "scenarios": scenarios,
            "brief": brief
        }


# Backward compatibility function
def run_pipeline(
    seeds: List[Dict[str, Any]],
    rules: List[Dict[str, Any]],
    metrics: Dict[str, Any] = None,
    config: Dict[str, Any] = None,
) -> Dict[str, Any]:
    """Backward compatibility function for the old API."""
    orchestrator = PipelineOrchestrator()
    if config:
        # Update config attributes if provided
        for key, value in config.items():
            if hasattr(orchestrator.config, key):
                setattr(orchestrator.config, key, value)
    return orchestrator.run_pipeline(seeds, rules, metrics)
