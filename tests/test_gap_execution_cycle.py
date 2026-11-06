"""Real-code tests for the bounded NGBSE gap -> evidence -> conclusion cycle."""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from ngbse20.research.gap_execution import (
    DOCUMENT_URL,
    _fetch,
    execute_cycle,
    make_case,
    perform_actions,
    reconcile,
)


def stub_cmd(cmd, timeout):
    assert timeout == 12
    if "-S" in cmd:
        return SimpleNamespace(
            returncode=1, stdout="",
            stderr="ModuleNotFoundError: No module named 'distutils'",
        )
    return SimpleNamespace(
        returncode=0,
        stdout="/python3.12/site-packages/setuptools/_distutils/__init__.py\n",
        stderr="",
    )


def stub_doc(url, timeout):
    assert url == DOCUMENT_URL and timeout == 12
    return {
        "status_code": 200,
        "final_url": DOCUMENT_URL,
        "bytes": b"<html><body>distutils package was removed. "
                 b"Setuptools package provides an alternative.</body></html>",
    }


def test_genuine_process_adapter_records_two_independent_conditions_and_doc():
    actions = perform_actions(
        run_command=stub_cmd, fetch=stub_doc, python_version=(3, 12)
    )
    assert [a["action_id"] for a in actions] == ["A1", "A2", "A3"]
    assert all(a["status"] == "completed" and a["executed_by_runner"] for a in actions)
    assert actions[0]["returncode"] == 1
    assert actions[1]["returncode"] == 0
    assert "_distutils" in actions[1]["stdout"]
    assert actions[2]["raw_sha256"] and actions[2]["extracted_snippets"]


def test_end_to_end_gap_test_evidence_reanalysis_and_refutation():
    cycle = execute_cycle(
        run_command=stub_cmd, fetch=stub_doc, python_version=(3, 12)
    )
    stages = [x["stage"] for x in cycle["trace"]]
    assert stages == [
        "gap", "test", "execution", "new_evidence",
        "reanalysis", "revised_conclusion",
    ]
    assert len(cycle["initial_case"]["sources"]) == 0
    assert len(cycle["after_case"]["sources"]) == 3
    assert cycle["verdict"]["status"] == "absolute_claim_refuted_in_test"
    assert cycle["verdict"]["evidence_ids"] == ["probe-A1", "probe-A2"]
    assert cycle["initial_analysis"]["investigation_status"] == "not_executed_by_engine"
    assert cycle["after_analysis"]["investigation_status"] == "not_executed_by_engine"
    assert not any(x.get("verified_execution") for x in cycle["after_analysis"]["reported_probe_results"])
    assert cycle["execution_receipts"][2]["meaning_verified"] is False


def test_failed_retrieval_is_not_silently_counted_as_source():
    def failure(url, timeout):
        raise OSError("network unavailable")

    cycle = execute_cycle(
        run_command=stub_cmd, fetch=failure, python_version=(3, 12)
    )
    assert cycle["trace"][2]["status"] == "partial"
    assert len(cycle["after_case"]["sources"]) == 2
    assert cycle["execution_receipts"][2]["executed_by_runner"] is False
    assert cycle["verdict"]["status"] == "absolute_claim_refuted_in_test"


def test_incomplete_testing_cannot_prove_an_absolute_claim():
    def failure(cmd, timeout):
        if "-S" in cmd:
            raise OSError("command unavailable")
        return stub_cmd(cmd, timeout)

    cycle = execute_cycle(run_command=failure, fetch=stub_doc, python_version=(3, 12))
    assert cycle["verdict"]["status"] == "not_established"
    assert cycle["verdict"]["evidence_ids"] == []


def test_same_returncode_without_counterexample_keeps_result_inconclusive():
    receipts = [
        {"action_id": "A1", "status": "completed", "returncode": 1},
        {"action_id": "A2", "status": "completed", "returncode": 1},
    ]
    assert reconcile(receipts)["status"] == "inconclusive"


def test_non_312_python_cannot_fake_environmental_result():
    with pytest.raises(RuntimeError, match="Python 3.12"):
        perform_actions(run_command=stub_cmd, fetch=stub_doc, python_version=(3, 11))


def test_retriever_rejects_all_other_urls():
    with pytest.raises(ValueError, match="allowlist"):
        _fetch("https://example.invalid/", timeout=2)


def test_question_remains_open_before_research_action():
    case = make_case()
    assert case["sources"] == [] and len(case["unknowns"]) == 1
    assert len(case["claims"]) == 1 and not case["claims"][0]["references"]
