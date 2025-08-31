from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Awaitable, Callable

import click

from ngbse20.collectors.async_http_collector import AsyncHTTPCollector
from ngbse20.collectors.http_collector import fetch as fetch_sync
from ngbse20.config.loader import load_seeds, validate_files
from ngbse20.export.stix import findings_to_stix
from ngbse20.runtime.logger import configure_logging

LOGGER = logging.getLogger(__name__)

@click.group()
@click.option("--log-level", default="INFO", help="DEBUG|INFO|WARNING|ERROR")
def cli(log_level: str) -> None:
    configure_logging(log_level)

@cli.command("validate-config")
@click.option("--seeds", required=True, type=click.Path(exists=True))
@click.option("--rules", required=True, type=click.Path(exists=True))
def validate_config_cmd(seeds: str, rules: str) -> None:
    try:
        n_seeds, n_rules = validate_files(seeds, rules)
    except Exception as e:
        click.echo(f"VALIDATION FAILED: {e}")
        raise SystemExit(1) from e
    click.echo(f"VALIDATION OK: {n_seeds} seeds, {n_rules} rules")

@cli.command()
@click.option("--seeds", required=True, type=click.Path(exists=True))
@click.option("--out", required=True, type=click.Path())
@click.option("--async", "use_async", is_flag=True, help="Gebruik async HTTP collector")
@click.option("--concurrency", default=10, show_default=True)
def collect(seeds: str, out: str, use_async: bool, concurrency: int) -> None:
    Path(out).mkdir(parents=True, exist_ok=True)
    seed_models = load_seeds(seeds)
    urls = [str(s.url) for s in seed_models]

    findings: list[dict[str, Any]] = []
    if use_async:
        async def run_async() -> list[dict[str, Any]]:
            c = AsyncHTTPCollector(max_concurrency=concurrency)
            return await c.collect(urls)

        runner: Callable[..., Awaitable[list[dict[str, Any]]]] = run_async
        findings = asyncio.run(runner())
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
def export_stix(findings: str, out: str) -> None:
    data = json.loads(Path(findings).read_text(encoding="utf-8"))
    bundle = findings_to_stix(data, score_lookup=None)
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8")
    click.echo(out)

if __name__ == "__main__":
    cli()
