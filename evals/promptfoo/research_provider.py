"""Promptfoo Python provider that invokes real repository code, without model APIs.

Scope:
  - NGBSE 20.1 legacy question selection, with a fixed LLM response.
  - BALLMS 50 offline research engine.
  - Shadowseed Gate evidence identities and seed lifecycle.
This does NOT execute the EAI Blindspot ChatGPT skill or prove research quality.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))


def _shadowseed_imports():
    # The CI workflow checks out a pinned Shadowseed commit. No copied engine.
    shadowseed_src = Path("/tmp/shadowseed-promptfoo/src")
    if not shadowseed_src.is_dir():
        raise RuntimeError("Shadowseed checkout missing; run via GitHub workflow")
    sys.path.insert(0, str(shadowseed_src))


def _legacy_questions(spec):
    from ngbse20.ballm.curiosity_generator import CuriosityGenerationEngine

    class FixedLLM:
        def __init__(self):
            self.called = False

        def call(self, *_args, **_kwargs):
            self.called = True
            return "What if a verified counterexample changes the entire conclusion?"

    stub = FixedLLM()
    engine = CuriosityGenerationEngine(stub)
    blindspots = spec["blindspots"]
    all_candidates = (
        engine._generate_coverage_curiosity_questions(blindspots)
        + engine._generate_recency_curiosity_questions(blindspots)
        + engine._generate_confidence_curiosity_questions(blindspots)
        + engine._generate_llm_curiosity_questions([], blindspots)
        + engine._generate_productive_failure_questions(blindspots)
    )
    selected = engine.generate_curiosity_questions([], blindspots)
    marker = "What if a verified counterexample"
    return {
        "llm_stub_called": stub.called,
        "all_candidates": len(all_candidates),
        "selected_count": len(selected),
        "model_question_in_candidates": any(marker in q["question"] for q in all_candidates),
        "model_question_selected": any(marker in q["question"] for q in selected),
        "selected_types": [q["type"] for q in selected],
    }


def _ballms50(spec):
    from ngbse20.ballms50 import analyze
    return analyze(spec["case"], question_budget=spec.get("budget", 12))


def _gate_keys(spec):
    _shadowseed_imports()
    from shadowseed.gate.runtime_adapter import _authority_signal_key
    from shadowseed.gate.signals import SignalKind, SignalDirection, ValidationSignal
    source = spec.get("source_ref", "paper:alpha")
    verified = spec.get("verified", True)
    direction = SignalDirection(spec.get("direction", "support"))
    retrieval = ValidationSignal(
        kind=SignalKind.RETRIEVAL, source_ref=source,
        verified=verified, direction=direction,
    )
    ssot = ValidationSignal(
        kind=SignalKind.SSOT, source_ref=source,
        verified=verified, direction=direction,
    )
    recurrence = ValidationSignal(
        kind=SignalKind.RECURRENCE, source_ref=source,
        verified=False, direction=direction,
    )
    return {
        "retrieval_key": _authority_signal_key(retrieval),
        "ssot_key": _authority_signal_key(ssot),
        "recurrence_key": _authority_signal_key(recurrence),
        "external": retrieval.is_external_evidence,
        "recurrence_external": recurrence.is_external_evidence,
    }


def _lifecycle(spec):
    _shadowseed_imports()
    from shadowseed.lifecycle import decay_traces, status_after_decay
    from shadowseed.models import SeedStatus
    turns = spec["turns"]
    seed = SimpleNamespace(
        trace=1.0, weight=0.0, status=SeedStatus(spec.get("status", "NEW")),
        turns_dormant=0,
    )

    class StubManager:
        def __init__(self):
            self._seeds = {"seed-a": seed}
            self.half_life_turns = 16
            self.dormant_threshold = 0.1
            self.config = SimpleNamespace(min_trace_for_gate=0.2)
            self.dormant_ttl_turns = 50
            self.events = []

        def _status_after_decay(self, item):
            return status_after_decay(self, item)

        def _set_authority(self, item, *, status):
            item.status = status

        def _touch_seed(self, item):
            pass

        def _record_and_sync(self, event, seed_id, **kwargs):
            self.events.append((event, seed_id, kwargs))

        def _record_event(self, event, seed_id, **kwargs):
            self.events.append((event, seed_id, kwargs))

        def expire_seed(self, *_args, **_kwargs):
            seed.status = SeedStatus.EXPIRED

    manager = StubManager()
    try:
        decay_traces(manager, turns_passed=turns)
        return {
            "trace": seed.trace,
            "status": seed.status.value,
            "event_count": len(manager.events),
            "half_life_met": math.isclose(seed.trace, 0.5, rel_tol=1e-12),
        }
    except (TypeError, ValueError) as exc:
        return {"rejected": True, "error_type": type(exc).__name__}


def call_api(prompt, options, context):
    try:
        spec = json.loads(prompt)
        target = spec["target"]
        if target == "ngbse_legacy":
            value = _legacy_questions(spec)
        elif target == "ballms50":
            value = _ballms50(spec)
        elif target == "shadowseed_gate":
            value = _gate_keys(spec)
        elif target == "shadowseed_lifecycle":
            value = _lifecycle(spec)
        else:
            raise ValueError(f"Unknown target: {target}")
        return {"output": json.dumps(value, sort_keys=True, ensure_ascii=False)}
    except Exception as exc:
        return {"error": f"{type(exc).__name__}: {exc}"}
