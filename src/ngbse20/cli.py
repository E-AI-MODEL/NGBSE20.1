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
from ngbse20.health import get_health_status, get_metrics, get_pipeline_status
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

@cli.command("health")
@click.option("--out", default="out", help="Output directory to check")
@click.option("--format", "output_format", default="text", type=click.Choice(["text", "json"]), help="Output format")
def health_cmd(out: str, output_format: str):
    """Check system health and status."""
    try:
        health_status = get_health_status(out)
        
        if output_format == "json":
            click.echo(json.dumps(health_status, indent=2))
        else:
            click.echo(f"🏥 System Health: {health_status['status'].upper()}")
            click.echo(f"⏰ Timestamp: {health_status['timestamp']}")
            click.echo(f"⏱️  Uptime: {health_status['uptime_seconds']} seconds")
            click.echo()
            
            for check_name, check_result in health_status.get("checks", {}).items():
                status_emoji = {
                    "healthy": "✅",
                    "warning": "⚠️",
                    "error": "❌",
                    "critical": "🚨"
                }.get(check_result.get("status", "unknown"), "❓")
                
                click.echo(f"{status_emoji} {check_name}: {check_result.get('status', 'unknown')}")
                if "message" in check_result:
                    click.echo(f"   📝 {check_result['message']}")
                
                # Show specific metrics for certain checks
                if check_name == "recent_activity" and check_result.get("findings_count"):
                    click.echo(f"   📊 Findings: {check_result['findings_count']}")
                elif check_name == "filesystem" and "disk_usage" in check_result:
                    disk = check_result["disk_usage"]
                    click.echo(f"   💾 Disk: {disk['used_gb']}GB / {disk['total_gb']}GB ({disk['usage_percent']}%)")
                elif check_name == "performance" and "cpu" in check_result:
                    cpu = check_result["cpu"]
                    click.echo(f"   🖥️  CPU: {cpu['usage_percent']}%")
                
                click.echo()
    
    except Exception as e:
        click.echo(f"❌ Health check failed: {e}")
        raise SystemExit(1) from e

@cli.command("metrics")
@click.option("--out", default="out", help="Output directory to check")
@click.option("--format", "output_format", default="text", type=click.Choice(["text", "json"]), help="Output format")
def metrics_cmd(out: str, output_format: str):
    """Get current performance metrics."""
    try:
        metrics = get_metrics(out)
        
        if output_format == "json":
            click.echo(json.dumps(metrics, indent=2))
        else:
            click.echo("📊 Performance Metrics")
            click.echo(f"⏰ Timestamp: {metrics['timestamp']}")
            click.echo(f"⏱️  Uptime: {metrics['uptime_seconds']} seconds")
            click.echo()
            
            if "error" in metrics:
                click.echo(f"❌ Error: {metrics['error']}")
            else:
                click.echo(f"🖥️  CPU Usage: {metrics.get('cpu_percent', 'N/A')}%")
                click.echo(f"💾 Memory Usage: {metrics.get('memory_percent', 'N/A')}%")
                
                if "disk_usage" in metrics:
                    disk = metrics["disk_usage"]
                    click.echo(f"💽 Disk Usage: {disk.get('usage_percent', 'N/A')}%")
                
                if "process_info" in metrics:
                    proc = metrics["process_info"]
                    click.echo(f"🔄 Process ID: {proc.get('pid', 'N/A')}")
                    click.echo(f"💾 Process Memory: {proc.get('memory_mb', 'N/A')} MB")
                    click.echo(f"🖥️  Process CPU: {proc.get('cpu_percent', 'N/A')}%")
    
    except Exception as e:
        click.echo(f"❌ Metrics collection failed: {e}")
        raise SystemExit(1) from e

@cli.command("status")
@click.option("--out", default="out", help="Output directory to check")
@click.option("--format", "output_format", default="text", type=click.Choice(["text", "json"]), help="Output format")
def status_cmd(out: str, output_format: str):
    """Get current pipeline status."""
    try:
        status = get_pipeline_status(out)
        
        if output_format == "json":
            click.echo(json.dumps(status, indent=2))
        else:
            status_emoji = {
                "active": "🟢",
                "recent": "🟡",
                "idle": "⚪",
                "error": "🔴"
            }.get(status.get("status", "unknown"), "❓")
            
            click.echo(f"{status_emoji} Pipeline Status: {status.get('status', 'unknown').upper()}")
            click.echo(f"📝 {status.get('message', 'No message available')}")
            
            if status.get("last_run"):
                click.echo(f"🕐 Last Run: {status['last_run']}")
            
            if status.get("time_since_last_seconds"):
                hours = status["time_since_last_seconds"] / 3600
                click.echo(f"⏰ Time Since Last Run: {hours:.1f} hours")
    
    except Exception as e:
        click.echo(f"❌ Status check failed: {e}")
        raise SystemExit(1) from e

if __name__ == "__main__":
    cli()
