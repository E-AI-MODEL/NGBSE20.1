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

LOGGER = logging.getLogger(__name__)

@click.group()
@click.option("--log-level", default="INFO", help="DEBUG|INFO|WARNING|ERROR")
def cli(log_level: str):
    configure_logging(log_level)

@cli.command("validate-config")
@click.option("--seeds", required=True, type=click.Path(exists=True))
@click.option("--rules", required=True, type=click.Path(exists=True))
def validate_config_cmd(seeds: str, rules: str):
    try:
        n_seeds, n_rules = validate_files(seeds, rules)
    except Exception as e:
        click.echo(f"VALIDATION FAILED: {e}")
        raise SystemExit(1) from e
    click.echo(f"VALIDATION OK: {n_seeds} seeds, {n_rules} rules")

@cli.command()
@click.option("--seeds", required=True, type=click.Path(exists=True))
@click.option("--out", required=True, type=click.Path())
@click.option("--async", "use_async", is_flag=True, help="Use async HTTP collector")
@click.option("--concurrency", default=10, show_default=True)
def collect(seeds: str, out: str, use_async: bool, concurrency: int):
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
