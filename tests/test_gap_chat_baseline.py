"""A partial model completion cannot count as a successful baseline."""
from __future__ import annotations

import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research" / "gap_cycle"))
from chat_baseline import compare_chat  # noqa: E402


def example_cycle():
    return {
        "case_id": "distutils-312-context",
        "initial_case": {
            "question": "Kan Python 3.12 overal distutils importeren?",
            "claims": [{"text": "Python 3.12 kan nergens distutils importeren."}],
        },
        "execution_receipts": [
            {"action_id": "A1", "status": "completed",
             "executed_by_runner": True, "returncode": 1,
             "stdout": "", "stderr": "ModuleNotFoundError", "condition": "isolated_no_site"},
            {"action_id": "A2", "status": "completed",
             "executed_by_runner": True, "returncode": 0,
             "stdout": "/setuptools/_distutils/__init__.py", "stderr": "",
             "condition": "installed_setuptools"},
            {"action_id": "A3", "status": "completed",
             "executed_by_runner": True, "url": "https://docs.python.org/3.12/whatsnew/3.12.html",
             "extracted_snippets": ["setuptools provides distutils"],
             "raw_sha256": "a" * 64, "http_status": 200},
        ],
    }


class MockClient:
    def __init__(self, status="completed"):
        self.calls = 0
        self.status = status
        self.responses = self

    def create(self, **kwargs):
        assert kwargs["model"] == "gpt-4.1-mini"
        assert kwargs["store"] is False
        self.calls += 1
        return SimpleNamespace(
            status=self.status,
            output_text="Controleer A1 en A2. Dit is geen bewijs voor andere installaties.",
            model="gpt-4.1-mini-2025-04-14", id=f"resp-{self.calls}",
            usage=SimpleNamespace(model_dump=lambda: {
                "input_tokens": 100, "output_tokens": 33,
            }),
        )


def test_two_completed_chat_rounds_store_verifiable_receipts(tmp_path):
    client = MockClient()
    out = tmp_path / "baseline"
    result = compare_chat(example_cycle(), client, out)
    assert client.calls == 2
    assert result["provider_calls"] == 2
    assert result["experimental_execution_by_chat"] is False
    assert result["same_receipts_as_ngbse"] is True
    assert (out / "chat_baseline.json").is_file()
    events = [json.loads(x) for x in (out / "chat_provider_events.jsonl").read_text().splitlines()]
    assert [e["kind"] for e in events] == [
        "request_start", "response", "request_start", "response"
    ]
    assert events[0]["messages"][1]["content"].find("A1") == -1
    assert "A1" in events[2]["messages"][-1]["content"]


def test_incomplete_model_response_is_not_reported_as_completed(tmp_path):
    client = MockClient(status="incomplete")
    out = tmp_path / "incomplete"
    with pytest.raises(RuntimeError, match="incomplete"):
        compare_chat(example_cycle(), client, out)
    assert client.calls == 1
    assert not (out / "chat_baseline.json").exists()


def test_baseline_cannot_silently_repeat_paid_requests(tmp_path):
    client = MockClient()
    out = tmp_path / "already"
    out.mkdir()
    with pytest.raises(ValueError, match="repeat"):
        compare_chat(example_cycle(), client, out)
    assert client.calls == 0
