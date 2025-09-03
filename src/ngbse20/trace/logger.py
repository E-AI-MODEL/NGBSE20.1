"""Trace logger."""

from __future__ import annotations

import datetime
import uuid
from typing import Any


def now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def event(  # noqa: PLR0913
    component: str,
    input: dict[str, Any],
    output: dict[str, Any],
    reasoning: str,
    rules_fired: list[str] | None = None,
    seeds_used: list[str] | None = None,
    metrics: dict[str, Any] | None = None,
    rubric: dict[str, float] | None = None,
) -> dict[str, Any]:
    return {
        "id": f"evt_{uuid.uuid4().hex[:12]}",
        "timestamp": now_iso(),
        "component": component,
        "input": input,
        "output": output,
        "reasoning": reasoning,
        "rules_fired": rules_fired or [],
        "seeds_used": seeds_used or [],
        "metrics": metrics or {},
        "rubric": rubric or {},
        "meta": {},
    }
