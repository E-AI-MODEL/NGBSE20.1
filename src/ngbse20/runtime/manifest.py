from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any

from ngbse20.logging import get_logger

LOGGER = get_logger(__name__)


@dataclass
class Manifest:
    run_id: str
    started_at: str
    finished_at: str
    inputs: dict[str, Any]
    outputs: dict[str, Any]
    stats: dict[str, Any]


def now_iso() -> str:
    return datetime.now(UTC).isoformat()


def write_manifest(
    run_id: str,
    *,
    inputs: dict[str, Any],
    outputs: dict[str, Any],
    stats: dict[str, Any] | None = None,
    path: str = "MANIFEST.json",
) -> str:
    manifest = Manifest(
        run_id=run_id,
        started_at=inputs.get("_started_at") or now_iso(),
        finished_at=now_iso(),
        inputs={k: v for k, v in inputs.items() if not k.startswith("_")},
        outputs=outputs,
        stats=stats or {},
    )
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(asdict(manifest), fh, ensure_ascii=False, indent=2)
    LOGGER.info("Wrote manifest to %s", path)
    return path
