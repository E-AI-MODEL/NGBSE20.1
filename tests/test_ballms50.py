"""Regression tests for BALLMS 50's offline research engine."""
import copy
import pytest

from ngbse20.ballms50 import InputError, analyze


def case():
    text = "Bron A stelt dat het programma werkt."
    return {"study_id": "example", "question": "Werkt het?", "sources": [
        {"id": "s1", "origin_id": "primary-a", "type": "report", "text": text},
        {"id": "s1-copy", "origin_id": "primary-a", "type": "report", "text": text},
    ], "claims": [{"id": "c1", "text": "Het programma werkt", "references": [
        {"source_id": "s1", "start": 0, "end": 6, "quote": "Bron A"},
        {"source_id": "s1-copy", "start": 0, "end": 6, "quote": "Bron A"},
    ]}], "required_source_types": ["report", "interview"]}


def test_same_origin_does_not_count_as_two_sources():
    result = analyze(case())
    assert result["claim_checks"][0]["distinct_reported_origins"] == 1
    assert result["claim_checks"][0]["semantic_support"] == "NOT_EVALUATED"
    assert {g["kind"] for g in result["gaps"]} >= {"corroboration", "source_coverage"}


def test_invalid_quote_does_not_prove_support():
    x = case()
    x["claims"][0]["references"][0]["quote"] = "Wrong"
    result = analyze(x)
    assert result["claim_checks"][0]["citation_state"] == "reference_error"
    assert "invalid_reference" in {g["kind"] for g in result["gaps"]}


def test_no_sources_is_not_proof_of_no_evidence():
    result = analyze({"question": "Wat weten we?", "sources": [], "claims": []})
    assert any(g["kind"] == "no_sources" for g in result["gaps"])
    assert result["investigation_status"] == "not_executed_by_engine"


def test_failed_and_empty_search_become_open_questions():
    x = case()
    x["search_attempts"] = [{"id": "a1", "status": "no_results", "query": "topic"},
                            {"id": "a2", "status": "error", "query": "topic"}]
    result = analyze(x)
    gaps = [g for g in result["gaps"] if g["kind"] == "search_unresolved"]
    assert len(gaps) == 2
    assert all(g["evidence_status"] == "open" for g in gaps)


def test_declared_conflict_is_not_asserted_as_truth():
    x = case()
    x["claims"].append({"id": "c2", "text": "Het programma werkt niet", "contradicts": ["c1"]})
    result = analyze(x)
    assert len([g for g in result["gaps"] if g["kind"] == "reported_conflict"]) == 1
    assert all(c["truth_status"] == "NOT_EVALUATED" for c in result["claim_checks"])


def test_round_robin_selection_keeps_rejected_questions_visible():
    x = case()
    x["claims"] = [{"id": f"c{i}", "text": f"Stelling {i}"} for i in range(17)]
    x["unknowns"] = [{"id": "u1", "question": "Welke andere factoren ontbreken?"}]
    result = analyze(x, question_budget=4)
    assert len(result["selected_questions"]) == 4
    assert len(result["questions"]) == 19
    assert len(result["excluded_questions"]) == 15
    assert len({q["kind"] for q in result["questions"] if q["id"] in result["selected_questions"]}) >= 2


def test_reported_probes_not_mistaken_for_executed():
    x = case()
    first = analyze(x)["selected_questions"][0]
    x["probe_results"] = [{"question_id": first, "status": "complete", "new_source_ids": ["s1"]}]
    result = analyze(x)
    assert result["reported_probe_results"][0]["verified_execution"] is False
    assert result["trace"][-1]["executed_by_engine"] == 0


def test_broken_proposer_does_not_claim_success():
    def broken(_payload):
        raise RuntimeError("provider crashed")
    result = analyze(case(), proposer=broken)
    assert result["analysis_status"] == "partial"
    assert any(x["stage"] == "model_proposer" and x["status"] == "failed" for x in result["trace"])


def test_model_questions_must_refer_to_actual_gaps():
    def proposer(payload):
        return [{"gap_id": "invented", "question": "Welk bewijs heeft iemand?"},
                {"gap_id": payload["gaps"][0]["id"], "question": "Wat zegt een tweede, onafhankelijke bron over dit?"}]
    result = analyze(case(), proposer=proposer)
    model = [q for q in result["questions"] if q["origin"] == "model_unverified"]
    assert len(model) == 1
    assert model[0]["semantic_support"] == "NOT_EVALUATED"


def test_deterministic_and_no_input_mutation():
    x = case()
    original = copy.deepcopy(x)
    assert analyze(x) == analyze(x)
    assert x == original


def test_invalid_ids_and_unknown_refs_rejected():
    x = case()
    x["sources"].append(dict(x["sources"][0]))
    with pytest.raises(InputError):
        analyze(x)
    y = case()
    y["probe_results"] = [{"question_id": "not-selected", "status": "complete", "new_source_ids": []}]
    with pytest.raises(InputError):
        analyze(y)


def test_source_fingerprints_and_quote_fingerprints_are_present():
    result = analyze(case())
    assert len(result["source_checks"]) == 2
    assert len(result["source_checks"][0]["text_sha256"]) == 64
    assert len(result["claim_checks"][0]["references"][0]["quote_sha256"]) == 64
    assert result["source_checks"][0]["origin_authority"] == "NOT_VERIFIED"


def test_duplicate_probe_result_is_rejected():
    x = case()
    qid = analyze(x)["selected_questions"][0]
    x["probe_results"] = [{"question_id": qid, "status": "complete", "new_source_ids": []},
                          {"question_id": qid, "status": "complete", "new_source_ids": []}]
    with pytest.raises(InputError):
        analyze(x)


def test_budget_is_bounded_and_bool_is_invalid():
    with pytest.raises(InputError):
        analyze(case(), question_budget=True)
    with pytest.raises(InputError):
        analyze(case(), question_budget=51)


def test_unknown_contradiction_is_rejected():
    x = case()
    x["claims"][0]["contradicts"] = ["not-existing"]
    with pytest.raises(InputError):
        analyze(x)
