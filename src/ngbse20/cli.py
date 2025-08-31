from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path

import click

from ngbse20.collectors.async_http_collector import AsyncHTTPCollector
from ngbse20.collectors.http_collector import fetch as fetch_sync
from ngbse20.config.loader import load_seeds, validate_files
from ngbse20.export.stix import findings_to_stix
from ngbse20.runtime.logger import configure_logging
from ngbse20.runtime.orchestrator import run_pipeline

LOGGER = logging.getLogger(__name__)

@click.group()
@click.option("--log-level", default="INFO", help="DEBUG|INFO|WARNING|ERROR")
def cli(log_level: str):
    configure_logging(log_level)

@cli.command("run")
@click.option("--seeds", required=True, type=click.Path(exists=True), help="Path to seeds.jsonl file")
@click.option("--rules", required=True, type=click.Path(exists=True), help="Path to rules.json file")
@click.option("--outdir", default='out', show_default=True, help="Output directory for results")
@click.option("--allowlist", default='*', show_default=True, help="Comma-separated list of allowed domains")
@click.option("--metrics", default='{}', help="JSON string of runtime metrics")
def run_pipeline_cmd(seeds: str, rules: str, outdir: str, allowlist: str, metrics: str):
    """Run the full NGBSE pipeline from collection to reporting."""
    click.echo("Starting NGBSE 20.1 pipeline...")
    
    try:
        # Load and parse input files
        rules_data = json.loads(Path(rules).read_text("utf-8"))
        seeds_data = [json.loads(line) for line in Path(seeds).read_text("utf-8").splitlines() if line.strip()]
        metrics_data = json.loads(metrics)
    except Exception as e:
        click.echo(f"Error loading input files: {e}", err=True)
        raise click.Abort()

    # Parse allowlist
    allowlist_domains = [d.strip() for d in allowlist.split(',')]
    
    config = {
        "output_dir": outdir,
        "allowlist": allowlist_domains
    }

    # Run the complete pipeline
    result = run_pipeline(seeds=seeds_data, rules=rules_data, metrics=metrics_data, config=config)
    
    click.echo(f"Pipeline finished. Results are in '{outdir}'.")
    click.echo(f"Status: {result.get('status', 'unknown')}")
    if 'cai' in result:
        click.echo(f"CAI Score: {result.get('cai', 0.0):.3f}")
    if 'counts' in result:
        counts = result.get('counts', {})
        click.echo(f"Findings: {counts.get('findings', 0)}")
        click.echo(f"Scenarios: {counts.get('scenarios', 0)}")

@cli.command("validate-config")
@click.option("--seeds", required=True, type=click.Path(exists=True))
@click.option("--rules", required=True, type=click.Path(exists=True))
def validate_config_cmd(seeds: str, rules: str):
    """Validate the syntax and structure of seed and rule files."""
    try:
        n_seeds, n_rules = validate_files(seeds, rules)
        click.echo(f"Validation successful: Found {n_seeds} seeds and {n_rules} rules.")
    except Exception as e:
        click.echo(f"Validation FAILED: {e}", err=True)
        raise click.Abort()

@cli.command()
@click.option("--seeds", required=True, type=click.Path(exists=True))
@click.option("--out", required=True, type=click.Path())
@click.option("--async", "use_async", is_flag=True, help="Use async HTTP collector")
@click.option("--concurrency", default=10, show_default=True)
def collect(seeds: str, out: str, use_async: bool, concurrency: int):
    """Collect data from seeds using HTTP collectors."""
    Path(out).mkdir(parents=True, exist_ok=True)
    seed_models = load_seeds(seeds)
    urls = [str(s.url) for s in seed_models]

    findings: list[dict] = []
    if use_async:
        async def run():
            c = AsyncHTTPCollector(max_concurrency=concurrency)
            return await c.collect(urls)
        findings = asyncio.run(run())
    else:
        seen: set[str] = set()
        for u in urls:
            f = fetch_sync(u)
            if not f:
                continue
            if f["content_hash"] in seen:
                continue
            seen.add(f["content_hash"])
            findings.append(f)

    Path(out, "findings.json").write_text(
        json.dumps(findings, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    LOGGER.info("Wrote %d findings to %s", len(findings), out)

@cli.command()
@click.option("--findings", required=True, type=click.Path(exists=True))
@click.option("--out", required=True, type=click.Path())
def export_stix(findings: str, out: str):
    """Export findings to STIX 2.1 format."""
    data = json.loads(Path(findings).read_text(encoding="utf-8"))
    bundle = findings_to_stix(data, score_lookup=None)
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8")
    click.echo(out)

@cli.command()
@click.option("--findings", required=True, type=click.Path(exists=True))
@click.option("--out", required=True, type=click.Path())
@click.option("--depth", default=3, help="Depth of curiosity questions (1-5)")
def ballm_analyze(findings: str, out: str, depth: int):
    """Run BALLM analysis to generate epistemic insights and curiosity questions."""
    
    # Load findings
    data = json.loads(Path(findings).read_text(encoding="utf-8"))
    
    # Check if we have the required data structure
    if isinstance(data, dict):
        findings_data = data.get("findings", [])
        blindspots_data = data.get("blindspots", {})
        asset_scores_data = data.get("asset_scores", {})
    else:
        findings_data = data
        blindspots_data = {}
        asset_scores_data = {}
    
    # Generate BALLM meta-layer
    from ngbse20.ballm.meta_layer_generator import BALLMMetaLayerGenerator
    from ngbse20.llm_client import LLMClient
    
    ballm_generator = BALLMMetaLayerGenerator(LLMClient())
    meta_layer = ballm_generator.generate_meta_layer(
        findings_data,
        blindspots_data,
        asset_scores_data
    )
    
    # Save BALLM output
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(
        json.dumps(meta_layer, ensure_ascii=False, indent=2), 
        encoding="utf-8"
    )
    
    click.echo(f"BALLM analysis complete. Output saved to {out}")
    click.echo(f"Epistemic Humility Score: {meta_layer.get('epistemic_humility_score', 0.0):.3f}")
    click.echo(f"Curiosity Questions Generated: {len(meta_layer.get('curiosity_questions', []))}")

if __name__ == "__main__":
    cli()
