"""Read-only Promptfoo provider for NGBSE's recorded live-model answers.

Never calls the model again. Its output must come from a real provider receipt
written by run_three_arm.py. A passing structural check is not a quality score.
"""
from __future__ import annotations

import json
import os
from pathlib import Path


def _answers_file():
    explicit = os.environ.get("NGBSE_QUALITY_ANSWERS_FILE")
    if not explicit:
        raise RuntimeError("NGBSE_QUALITY_ANSWERS_FILE is required; no fake results")
    path = Path(explicit)
    if not path.is_file():
        raise FileNotFoundError(f"No actual provider outputs at {path}")
    return path


def call_api(prompt, options, context):
    try:
        request = json.loads(prompt)
        case_id, arm = request["case_id"], request["arm"]
        rows = json.loads(_answers_file().read_text(encoding="utf-8"))
        matches = [r for r in rows if r["case_id"] == case_id and r["arm"] == arm]
        if len(matches) != 1:
            return {"error": f"Missing or duplicated actual output for {case_id}/{arm}"}
        row = matches[0]
        data = {
            "case_id": case_id,
            "arm": arm,
            "questions": row["questions"],
            "analysis_status": row["analysis_status"],
            "model_used": row["model_used"],
            "model_status": row.get("model_status"),
            "trace_links": row.get("trace_links", []),
        }
        return {"output": json.dumps(data, ensure_ascii=False)}
    except Exception as exc:
        return {"error": f"{type(exc).__name__}: {exc}"}
