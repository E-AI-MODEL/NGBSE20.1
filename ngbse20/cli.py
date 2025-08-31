from __future__ import annotations
import argparse
import asyncio
import json
from pathlib import Path
from ngbse20.collectors.http_async import collect_urls
from ngbse20.export.stix import write_stix
from ngbse20.runtime.manifest import write_manifest, now_iso
from ngbse20.logging import get_logger

LOGGER = get_logger(__name__)

def _read_lines(p: Path) -> list[str]:
    return [x.strip() for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]

def main():
    ap = argparse.ArgumentParser("ngbse20")
    ap.add_argument("--urls", type=Path, required=True, help="Bestand met URLs (1 per regel)")
    ap.add_argument("--out-dir", type=Path, default=Path("out"))
    ap.add_argument("--concurrency", type=int, default=8)
    ap.add_argument("--user-agent", type=str, default=None)
    args = ap.parse_args()

    urls = _read_lines(args.urls)
    args.out_dir.mkdir(parents=True, exist_ok=True)

    LOGGER.info("Start collection for %d urls", len(urls))
    findings = asyncio.run(collect_urls(
        urls,
        concurrency=args.concurrency,
        user_agent=args.user_agent or "NGBSE20.1-Collector",
    ))

    findings_path = args.out_dir / "findings.json"
    with findings_path.open("w", encoding="utf-8") as fh:
        json.dump(findings, fh, ensure_ascii=False, indent=2)
    LOGGER.info("Saved findings: %s", findings_path)

    stix_path = args.out_dir / "bundle.stix2.json"
    write_stix(findings, str(stix_path))
    LOGGER.info("Saved STIX: %s", stix_path)

    write_manifest(
        run_id=now_iso(),
        inputs={"_started_at": now_iso(), "url_count": len(urls)},
        outputs={"findings": str(findings_path), "stix": str(stix_path)},
        stats={"collected": len(findings)},
        path=str(args.out_dir / "MANIFEST.json"),
    )

if __name__ == "__main__":
    main()
