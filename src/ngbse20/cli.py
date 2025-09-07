from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

import click
import requests

from ngbse20.collectors.http_web import HttpWebCollector
from ngbse20.config.loader import validate_files
from ngbse20.export.stix import findings_to_stix
from ngbse20.monitoring.health import get_health_status
from ngbse20.runtime.logger import configure_logging
from ngbse20.runtime.orchestrator import run_pipeline
from ngbse20.utils.validation import validate_allowlist

LOGGER = logging.getLogger(__name__)


@click.group()
@click.option("--log-level", default="INFO", help="DEBUG|INFO|WARNING|ERROR")
def cli(log_level: str):
    configure_logging(log_level)


@cli.command("run")
@click.option(
    "--seeds",
    required=True,
    type=click.Path(exists=True),
    help="Path to seeds.jsonl file",
)
@click.option(
    "--rules",
    required=True,
    type=click.Path(exists=True),
    help="Path to rules.json file",
)
@click.option("--outdir", default="out", show_default=True, help="Output directory for results")
@click.option(
    "--allowlist",
    default="*",
    show_default=True,
    help="Comma-separated list of allowed domains",
)
@click.option("--metrics", default="{}", help="JSON string of runtime metrics")
@click.option(
    "--export-formats",
    default="csv,html,docx",
    show_default=True,
    help="Comma-separated list of export formats (csv,html,docx,stix)",
)
def run_pipeline_cmd(seeds: str, rules: str, outdir: str, allowlist: str, metrics: str, export_formats: str):
    """Run the full NGBSE pipeline from collection to reporting."""
    click.echo("Starting NGBSE 20.3 pipeline...")

    try:
        # Load and parse input files
        rules_data = json.loads(Path(rules).read_text("utf-8"))
        seeds_data = [json.loads(line) for line in Path(seeds).read_text("utf-8").splitlines() if line.strip()]
        metrics_data = json.loads(metrics)
    except (FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError) as e:
        click.echo(f"Error loading input files: {e}", err=True)
        raise click.Abort()

        # Parse and validate allowlist
        allowlist_domains = [d.strip() for d in allowlist.split(",")]
        allowlist_domains = validate_allowlist(allowlist_domains)

        # Parse export formats
        export_formats_list = [f.strip() for f in export_formats.split(",")]
        valid_formats = ["csv", "html", "docx", "stix"]
        invalid_formats = [f for f in export_formats_list if f not in valid_formats]
        if invalid_formats:
            click.echo(f"Warning: Invalid export formats: {invalid_formats}", err=True)
            click.echo(f"Valid formats: {valid_formats}", err=True)
            export_formats_list = [f for f in export_formats_list if f in valid_formats]

    config = {
        "output_dir": outdir,
        "allowlist": allowlist_domains,
        "export": {"formats": export_formats_list, "output_dir": outdir},
    }

    # Run the complete pipeline
    result = run_pipeline(seeds=seeds_data, rules=rules_data, metrics=metrics_data, config=config)

    click.echo(f"Pipeline finished. Results are in '{outdir}'.")
    click.echo(f"Status: {result.get('status', 'unknown')}")
    if "cai" in result:
        click.echo(f"CAI Score: {result.get('cai', 0.0):.3f}")
    if "counts" in result:
        counts = result.get("counts", {})
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
    except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
        click.echo(f"Validation FAILED: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.option("--seeds", required=True, type=click.Path(exists=True))
@click.option("--out", required=True, type=click.Path())
@click.option(
    "--collector",
    default="web",
    help="Collector type to use (web, leakix, shodan, censys, urlscan, github, news)",
)
@click.option("--allowlist", default="*", help="Comma-separated list of allowed domains")
def collect(seeds: str, out: str, collector: str, allowlist: str):
    """Collect data from seeds using specified collector."""
    Path(out).mkdir(parents=True, exist_ok=True)

    try:
        # Load seeds
        seeds_data = [json.loads(line) for line in Path(seeds).read_text("utf-8").splitlines() if line.strip()]
    except (FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError) as e:
        click.echo(f"Error loading seeds: {e}", err=True)
        raise click.Abort()

        # Parse and validate allowlist
        allowlist_domains = [d.strip() for d in allowlist.split(",")]
        allowlist_domains = validate_allowlist(allowlist_domains)

    # Use appropriate collector
    if collector == "web":
        collector_instance = HttpWebCollector(allowlist_domains=allowlist_domains)
    else:
        click.echo(
            f"Collector type '{collector}' not yet implemented for " f"individual collection.",
            err=True,
        )
        click.echo("Use 'ngbse20 run' for full pipeline with all collectors.", err=True)
        raise click.Abort()

    # Collect data
    findings = []
    now_iso = datetime.now(timezone.utc).isoformat()

    for seed in seeds_data:
        try:
            seed_findings = collector_instance.collect(seed, now_iso)
            findings.extend(seed_findings)
        except (requests.RequestException, ValueError, KeyError) as e:
            click.echo(f"Error collecting from seed {seed.get('id', 'unknown')}: {e}", err=True)

    # Save findings
    findings_path = Path(out, "findings.json")
    findings_path.write_text(json.dumps(findings, ensure_ascii=False, indent=2), encoding="utf-8")

    click.echo(f"Collection complete. Found {len(findings)} items.")
    click.echo(f"Results saved to: {findings_path}")


@cli.command("export")
@click.option("--findings", required=True, type=click.Path(exists=True), help="Path to findings.json file")
@click.option("--output", required=True, type=click.Path(), help="Output path for exported file")
@click.option("--format", type=click.Choice(["csv", "html", "docx", "stix"]), default="html", help="Export format")
@click.option("--target", default="Unknown", help="Target name for the report")
def export_cmd(findings: str, output: str, format: str, target: str):
    """Export findings to various formats."""
    try:
        from ngbse20.runtime.orchestrator import PipelineOrchestrator

        # Load findings
        findings_data = json.loads(Path(findings).read_text("utf-8"))

        # Create orchestrator for export functionality
        orchestrator = PipelineOrchestrator()

        # Prepare export data
        export_data = {
            "findings": findings_data,
            "config": {"target": target, "timestamp": datetime.now(timezone.utc).isoformat()},
        }

        # Export data
        output_path = Path(output)
        success = orchestrator.export_data(export_data, output_path, format)

        if success:
            click.echo(f"Export successful: {output_path}")
        else:
            click.echo(f"Export failed: {output_path}", err=True)
            raise click.Abort()

    except Exception as e:
        click.echo(f"Export error: {e}", err=True)
        raise click.Abort()


@cli.command("export-stix")
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
    from ngbse20.config.loader import load_config
    from ngbse20.llm_client import LLMClient

    # Load configuration for BALLM
    config = load_config()
    ballm_generator = BALLMMetaLayerGenerator(LLMClient(config=config.__dict__))
    meta_layer = ballm_generator.generate_meta_layer(findings_data, blindspots_data, asset_scores_data)

    # Save BALLM output
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(json.dumps(meta_layer, ensure_ascii=False, indent=2), encoding="utf-8")

    click.echo(f"BALLM analysis complete. Output saved to {out}")
    click.echo(f"Epistemic Humility Score: " f"{meta_layer.get('epistemic_humility_score', 0.0):.3f}")
    click.echo(f"Curiosity Questions Generated: " f"{len(meta_layer.get('curiosity_questions', []))}")


@cli.command("collectors")
def list_collectors():
    """List all available collectors and their status."""
    from ngbse20.collectors import (
        CensysCollector,
        GitHubCollector,
        HttpWebCollector,
        LeakIXCollector,
        NewsCollector,
        ShodanCollector,
        URLScanCollector,
    )

    collectors = [
        ("HttpWebCollector", HttpWebCollector, []),
        ("LeakIX", LeakIXCollector, ["LEAKIX_API_KEY"]),
        ("Shodan", ShodanCollector, ["SHODAN_API_KEY"]),
        ("Censys", CensysCollector, ["CENSYS_API_ID", "CENSYS_API_SECRET"]),
        ("URLScan", URLScanCollector, ["URLSCAN_API_KEY"]),
        ("GitHub", GitHubCollector, ["GITHUB_TOKEN"]),
        ("News", NewsCollector, ["NEWS_API_KEY"]),
    ]

    click.echo("Available NGBSE 20.3 Collectors:")
    click.echo("=" * 50)

    for name, _collector_class, required_envs in collectors:
        # Check if required environment variables are set
        env_status = "✅" if all(os.getenv(env) for env in required_envs) else "❌"
        status = "Active" if env_status == "✅" else "Inactive (missing API keys)"

        click.echo(f"{name:<15} {env_status} {status}")
        if required_envs:
            click.echo(f"{'':15}   Requires: {', '.join(required_envs)}")
        click.echo()


@cli.command("health")
@click.option(
    "--format",
    "output_format",
    default="text",
    type=click.Choice(["text", "json"]),
    help="Output format",
)
def health_check(output_format: str):
    """Check the health status of NGBSE components."""
    try:
        health_data = get_health_status()

        if output_format == "json":
            click.echo(json.dumps(health_data, indent=2))
        else:
            # Text format
            status_emoji = {"healthy": "✅", "degraded": "⚠️", "unhealthy": "❌"}

            overall_status = health_data["status"]
            click.echo(f"Overall Status: {status_emoji.get(overall_status, '❓')} " f"{overall_status.upper()}")
            click.echo(f"Uptime: {health_data['uptime_seconds']:.1f} seconds")
            click.echo()

            # System metrics
            metrics = health_data["metrics"]
            click.echo("System Metrics:")
            click.echo(f"  CPU: {metrics['cpu_percent']:.1f}%")
            click.echo(f"  Memory: {metrics['memory_percent']:.1f}%")
            click.echo(f"  Disk: {metrics['disk_percent']:.1f}%")
            click.echo()

            # Health checks
            click.echo("Component Health:")
            for check in health_data["checks"]:
                emoji = status_emoji.get(check["status"], "❓")
                click.echo(f"  {emoji} {check['name']}: {check['message']}")
                if check.get("details"):
                    for key, value in check["details"].items():
                        if isinstance(value, list):
                            click.echo(f"    {key}: {', '.join(map(str, value))}")
                        else:
                            click.echo(f"    {key}: {value}")

    except (OSError, ImportError, AttributeError) as e:
        click.echo(f"Health check failed: {e}", err=True)
        raise click.Abort()


if __name__ == "__main__":
    cli()
