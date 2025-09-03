"""Simple rules engine."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

OPS: dict[str, Callable[[Any, Any], bool]] = {
    ">": lambda a, b: a > b,
    "<": lambda a, b: a < b,
    ">=": lambda a, b: a >= b,
    "<=": lambda a, b: a <= b,
    "==": lambda a, b: a == b,
    "!=": lambda a, b: a != b,
}


def parse_condition(cond: str) -> tuple[str, float | str]:
    v: float | str
    for op in (">=", "<=", ">", "<", "==", "!="):
        if op in cond:
            val = cond.split(op, 1)[1].strip()
            try:
                v = float(val)
            except Exception:
                v = val
            return op, v
    try:
        v = float(cond)
    except Exception:
        v = cond
    return "==", v


def trigger_matches(trigger: dict[str, str], metrics: dict[str, Any]) -> bool:
    for k, cond in trigger.items():
        if k not in metrics:
            return False
        op, v = parse_condition(str(cond))
        x = metrics.get(k)
        if x is None:
            return False
        if isinstance(v, float):
            try:
                x = float(x)
            except Exception:
                return False
        op_func = OPS.get(op)
        if op_func is None:
            return False
        try:
            result = op_func(x, v)
        except Exception:
            result = False
        if not result:
            return False
    return True


def evaluate_rules(rules: list[dict[str, Any]], metrics: dict[str, Any]) -> list[dict[str, Any]]:
    actions = []
    for r in rules:
        if trigger_matches(r.get("trigger", {}), metrics):
            act = dict(r.get("action", {}))
            act["rule_id"] = r.get("id")
            actions.append(act)
    return actions
