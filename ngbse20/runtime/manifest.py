from __future__ import annotations
import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from ngbse20.logging import get_logger

LOGGER = get_logger(__name__)

@dataclass
class Manifest:
    run_id: str
    started_at: str
    finished_at: str
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]
    stats: Dict[str, Any]

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def write_manifest(
    run_id: str,
    *,
    inputs: Dict[str, Any],
    outputs: Dict[str, Any],
    stats: Optional[Dict[str, Any]] = None,
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
