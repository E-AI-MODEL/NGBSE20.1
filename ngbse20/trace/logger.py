"""Trace logger."""
from typing import Dict, Any, List
from datetime import datetime, timezone
import uuid

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def event(component: str, input: Dict[str, Any], output: Dict[str, Any], reasoning: str,
          rules_fired: List[str]|None=None, seeds_used: List[str]|None=None,
          metrics: Dict[str, Any]|None=None, rubric: Dict[str, float]|None=None) -> Dict[str, Any]:
    return {
        "id": f"evt_{uuid.uuid4().hex[:12]}",
        "timestamp": now_iso(),
        "component": component,
        "input": input, "output": output, "reasoning": reasoning,
        "rules_fired": rules_fired or [],
        "seeds_used": seeds_used or [],
        "metrics": metrics or {},
        "rubric": rubric or {},
        "meta": {}
    }
