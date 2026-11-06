"""BALLMS 50 research engine. No network calls, no inferred truth claims.

A citation match establishes a textual link, not support for the meaning of a claim.
Proposed research questions are suggestions, never evidence or completed searches.
"""

from __future__ import annotations

from collections import defaultdict
from hashlib import sha256
import json
from typing import Any, Callable

VERSION = "50.0.0-research"
MAX_SOURCES = 100
MAX_CLAIMS = 250
MAX_SOURCE_CHARS = 200_000
MAX_QUESTIONS = 50


class InputError(ValueError):
    """The supplied research case does not match the offline contract."""


def _digest(value: Any) -> str:
    return sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _items(value: Any, label: str, limit: int) -> list[dict[str, Any]]:
    if not isinstance(value, list) or len(value) > limit or any(not isinstance(x, dict) for x in value):
        raise InputError(f"{label} must be a list of at most {limit} objects")
    return value


def _indexed(rows: list[dict[str, Any]], label: str) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for item in rows:
        key = item.get("id")
        if not isinstance(key, str) or not key.strip() or len(key) > 128 or key in out:
            raise InputError(f"{label} requires unique nonempty ids (max 128 characters)")
        out[key] = item
    return out


def _gap(kind: str, subject: str, detail: str, *, source_ids: list[str] | None = None, question: str = "", priority: int = 2) -> dict[str, Any]:
    return {
        "id": "G-" + _digest([kind, subject, detail])[:12],
        "kind": kind,
        "subject": subject,
        "detail": detail,
        "source_ids": sorted(set(source_ids or [])),
        "proposed_question": question,
        "priority": priority,  # queue ordering, not probability or confidence
        "evidence_status": "open",
    }


def _candidate(gap: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": "Q-" + _digest([gap["id"], gap["proposed_question"]])[:12],
        "gap_id": gap["id"],
        "kind": gap["kind"],
        "question": gap["proposed_question"],
        "priority": gap["priority"],
        "source_ids": gap["source_ids"],
        "origin": "rule",
        "state": "candidate",
        "semantic_support": "NOT_EVALUATED",
    }


def _select(candidates: list[dict[str, Any]], budget: int) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    """Round-robin over question families, retaining every rejected candidate."""
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in candidates:
        groups[item["kind"]].append(item)
    for items in groups.values():
        items.sort(key=lambda q: (-q["priority"], q["id"]))
    kinds = sorted(groups, key=lambda k: (-max(q["priority"] for q in groups[k]), k))
    selected: list[dict[str, Any]] = []
    while len(selected) < budget and any(groups.values()):
        for kind in kinds:
            if groups[kind] and len(selected) < budget:
                selected.append(groups[kind].pop(0))
    chosen = {q["id"] for q in selected}
    rejected = [{"question_id": q["id"], "reason": "budget_limit"} for q in candidates if q["id"] not in chosen]
    return selected, rejected


def analyze(case: dict[str, Any], *, question_budget: int = 12,
            proposer: Callable[[dict[str, Any]], list[dict[str, Any]]] | None = None) -> dict[str, Any]:
    """Generate traceable gaps and proposed questions from supplied research material.

    The optional proposer is an injected adapter. This engine never chooses a remote
    model or silently switches providers. Caller-provided results are reported data.
    """
    if not isinstance(case, dict):
        raise InputError("case must be a JSON object")
    if type(question_budget) is not int or not (1 <= question_budget <= MAX_QUESTIONS):
        raise InputError(f"question_budget must be between 1 and {MAX_QUESTIONS}")
    sources = _indexed(_items(case.get("sources", []), "sources", MAX_SOURCES), "sources")
    claims = _indexed(_items(case.get("claims", []), "claims", MAX_CLAIMS), "claims")
    attempts = _indexed(_items(case.get("search_attempts", []), "search_attempts", 250), "search_attempts")
    unknowns = _indexed(_items(case.get("unknowns", []), "unknowns", 250), "unknowns")
    _items(case.get("probe_results", []), "probe_results", 250)

    for source in sources.values():
        if not isinstance(source.get("text", ""), str) or len(source.get("text", "")) > MAX_SOURCE_CHARS:
            raise InputError("each source.text must be a string at most 200000 characters")
        if not isinstance(source.get("type", "unknown"), str):
            raise InputError("each source.type must be a string")
    wanted = case.get("required_source_types", [])
    if not isinstance(wanted, list) or len(wanted) > 50 or any(not isinstance(x, str) or not x.strip() for x in wanted):
        raise InputError("required_source_types must be a list of strings")
    trace: list[dict[str, Any]] = [{"stage": "input", "status": "ok", "sources": len(sources), "claims": len(claims), "input_sha256": _digest(case)}]
    source_checks = [{"source_id": sid, "source_type": source.get("type", "unknown"),
                      "text_sha256": sha256(source.get("text", "").encode()).hexdigest(),
                      "reported_origin_id": source.get("origin_id") or sid,
                      "origin_authority": "NOT_VERIFIED"}
                     for sid, source in sorted(sources.items())]
    claim_checks: list[dict[str, Any]] = []
    gaps: list[dict[str, Any]] = []

    for claim_id, claim in sorted(claims.items()):
        statement = claim.get("text")
        if not isinstance(statement, str) or not statement.strip():
            raise InputError(f"claim {claim_id} needs text")
        refs = _items(claim.get("references", []), f"claim {claim_id}.references", 50)
        checks: list[dict[str, Any]] = []
        valid_ids: list[str] = []
        for ref in refs:
            sid = ref.get("source_id")
            source = sources.get(sid) if isinstance(sid, str) else None
            start, end, quote = ref.get("start"), ref.get("end"), ref.get("quote")
            exact = (source is not None and type(start) is int and type(end) is int and
                     isinstance(quote, str) and 0 <= start < end <= len(source.get("text", "")) and
                     source["text"][start:end] == quote)
            checks.append({"source_id": sid, "status": "exact_quote" if exact else "invalid_reference",
                           "quote_sha256": sha256(quote.encode()).hexdigest() if exact else None,
                           "semantic_support": "NOT_EVALUATED"})
            if exact:
                valid_ids.append(sid)
        origin_groups = {str(sources[sid].get("origin_id") or sid) for sid in valid_ids}
        state = "no_reference" if not refs else "exact_quote" if len(valid_ids) == len(refs) else "reference_error"
        claim_checks.append({"claim_id": claim_id, "citation_state": state, "references": checks,
                             "distinct_reported_origins": len(origin_groups), "semantic_support": "NOT_EVALUATED",
                             "truth_status": "NOT_EVALUATED"})
        label = statement.strip()[:140]
        if state == "no_reference":
            gaps.append(_gap("missing_evidence", claim_id, "Claim has no cited source", question=f"Welke bron onderbouwt de bewering: {label}?", priority=5))
        if state == "reference_error":
            gaps.append(_gap("invalid_reference", claim_id, "At least one quote or source handle is invalid", source_ids=valid_ids,
                             question=f"Welke exacte bronpassage onderbouwt de bewering: {label}?", priority=6))
        if refs and len(origin_groups) < 2:
            gaps.append(_gap("corroboration", claim_id, "Fewer than two distinct reported origins with exact quotes", source_ids=valid_ids,
                             question=f"Welke onafhankelijke bron kan de bewering toetsen: {label}?", priority=3))

    # Conflicts are explicitly reported by the input, never inferred as factual.
    pairs: set[tuple[str, str]] = set()
    for cid, claim in claims.items():
        conflicts = claim.get("contradicts", [])
        if not isinstance(conflicts, list):
            raise InputError(f"claim {cid}.contradicts must be a list")
        for target in conflicts:
            if not isinstance(target, str) or target not in claims or target == cid:
                raise InputError(f"claim {cid} references an unknown or identical contradicts id")
            pairs.add(tuple(sorted((cid, target))))
    for a, b in sorted(pairs):
        gaps.append(_gap("reported_conflict", f"{a}/{b}", "Contradiction declared by input; semantic conflict not checked",
                         question=f"Welke brongegevens helpen het opgegeven verschil tussen {a} en {b} te verklaren?", priority=6))

    types_present = {str(s.get("type", "unknown")).lower() for s in sources.values()}
    for source_type in sorted({x.lower() for x in wanted} - types_present):
        gaps.append(_gap("source_coverage", source_type, "Required source type has no supplied records",
                         question=f"Welke {source_type}-bronnen ontbreken in dit onderzoek, en waar zijn ze te vinden?", priority=4))
    if not sources:
        gaps.append(_gap("no_sources", "study", "No sources supplied; this is not evidence of absence",
                         question="Welke eerste bron kan de onderzoeksvraag toetsbaar maken?", priority=6))
    for aid, attempt in sorted(attempts.items()):
        status = attempt.get("status")
        if status not in ("no_results", "error", "complete", "skipped"):
            raise InputError(f"search_attempt {aid} has invalid status")
        if status in ("no_results", "error"):
            query = str(attempt.get("query", ""))[:140]
            gaps.append(_gap("search_unresolved", aid, f"Reported search status: {status}; not proof that evidence does not exist",
                             question=f"Welke andere zoekstrategie kan deze vraag toetsen: {query}?", priority=4))
    for uid, unknown in sorted(unknowns.items()):
        question = unknown.get("question")
        if not isinstance(question, str) or not question.strip():
            raise InputError(f"unknown {uid} needs a question")
        gaps.append(_gap("open_question", uid, str(unknown.get("reason", "Explicitly open question"))[:300],
                         question=question.strip(), priority=5))
    trace.append({"stage": "evidence", "status": "ok", "claims_checked": len(claim_checks), "gaps_found": len(gaps),
                  "note": "Exact quotes and reported origins are not semantic or independent validation"})

    candidates = [_candidate(g) for g in gaps]
    model_status = "not_requested"
    if proposer is not None:
        model_status = "ok"
        try:
            suggestions = proposer({"study_id": case.get("study_id", ""), "question": case.get("question", ""),
                                    "gaps": [{k: v for k, v in g.items() if k != "proposed_question"} for g in gaps],
                                    "claims": [{"id": k, "text": v["text"]} for k, v in sorted(claims.items())]})
            if not isinstance(suggestions, list):
                raise ValueError("proposer must return a list")
            allowed_gap_ids = {g["id"] for g in gaps}
            for suggestion in suggestions[:MAX_QUESTIONS]:
                if not isinstance(suggestion, dict) or suggestion.get("gap_id") not in allowed_gap_ids:
                    continue
                question = suggestion.get("question")
                if not isinstance(question, str) or not (8 <= len(question.strip()) <= 500):
                    continue
                item = {"id": "Q-" + _digest([suggestion["gap_id"], question.strip()])[:12],
                        "gap_id": suggestion["gap_id"], "kind": "model_suggestion", "question": question.strip(),
                        "priority": 3, "source_ids": [], "origin": "model_unverified", "state": "candidate",
                        "semantic_support": "NOT_EVALUATED"}
                if not any(q["id"] == item["id"] for q in candidates):
                    candidates.append(item)
        except Exception as exc:
            model_status = "failed"
            trace.append({"stage": "model_proposer", "status": "failed", "error_type": type(exc).__name__})
    trace.append({"stage": "model_proposer", "status": model_status})
    selected, excluded = _select(candidates, question_budget)
    trace.append({"stage": "question_selection", "status": "ok", "candidates": len(candidates),
                  "selected": len(selected), "excluded": len(excluded), "budget": question_budget})

    # This stage only records user-supplied status; the engine does not execute probes.
    reported: list[dict[str, Any]] = []
    selected_ids = {q["id"] for q in selected}
    recorded_qids: set[str] = set()
    for p in case.get("probe_results", []):
        qid = p.get("question_id")
        if qid not in selected_ids or qid in recorded_qids:
            raise InputError("probe_result must reference a unique selected question")
        recorded_qids.add(qid)
        state = p.get("status")
        if state not in ("complete", "no_results", "error", "skipped"):
            raise InputError("probe_result has invalid status")
        ids = p.get("new_source_ids", [])
        if not isinstance(ids, list) or any(s not in sources for s in ids):
            raise InputError("probe_result source ids must exist in the case")
        reported.append({"question_id": qid, "reported_status": state, "reported_source_ids": sorted(set(ids)),
                         "verified_execution": False, "independent_evidence_review": "NOT_EVALUATED"})
    trace.append({"stage": "probe_results", "status": "reported_only", "count": len(reported),
                  "executed_by_engine": 0})
    analysis_status = "partial" if model_status == "failed" else "analysis_complete"
    return {
        "version": VERSION,
        "study_id": str(case.get("study_id", "")),
        "analysis_status": analysis_status,
        "investigation_status": "not_executed_by_engine",
        "source_checks": source_checks,
        "claim_checks": claim_checks,
        "gaps": gaps,
        "questions": candidates,
        "selected_questions": [q["id"] for q in selected],
        "excluded_questions": excluded,
        "probes": [{"question_id": q["id"], "query": q["question"], "status": "proposed_not_run"} for q in selected],
        "reported_probe_results": reported,
        "trace": trace,
        "output_sha256": _digest([source_checks, claim_checks, gaps, candidates, [q["id"] for q in selected], reported]),
    }
