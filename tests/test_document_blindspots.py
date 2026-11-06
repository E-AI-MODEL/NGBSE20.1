"""Tests for the document path; no provider or network calls are required."""

import json

import pytest
from click.testing import CliRunner

from ngbse20.cli import cli
from ngbse20.research import BALLMDocumentProposer, analyze_document


def packet():
    return {
        "question": "Wat volgt uit dit onderzoeksverslag?",
        "sources": [{
            "id": "paper", "design": "observational",
            "text": "Leerlingen rapporteerden betere huiswerkcijfers. Zelfstandige toetsing is niet gemeten."
        }],
        "claims": [{
            "id": "c1",
            "text": "De leerlingen hebben zelfstandige vaardigheden geleerd.",
            "claim_type": "learning",
            "references": [{"source_id": "paper", "quote": "betere huiswerkcijfers"}],
        }],
        "gaps": [{
            "id": "gap1",
            "description": "Een onafhankelijke hertoets ontbreekt in de beschrijving.",
            "why_it_matters": "Een huiswerkcijfer meet niet vanzelf zelfstandig leren.",
            "next_test": "Wat presteren leerlingen later zonder AI?",
            "anchors": [{"source_id": "paper", "quote": "Zelfstandige toetsing is niet gemeten."}],
        }],
    }


def test_located_quote_is_not_treated_as_semantic_proof():
    result = analyze_document(packet())
    assert result["status"] == "complete"
    claim = result["claims"][0]
    assert claim["evidence_status"] == "quote_anchored_not_verified"
    assert claim["semantic_support_verified"] is False
    assert "causal_or_learning_inference_requires_stronger_evidence" in claim["limits"]
    source = packet()["sources"][0]["text"]
    ref = claim["references"][0]
    assert source[ref["start"]:ref["end"]] == ref["quote"]
    assert ref["meaning_verified"] is False
    assert any(x["basis"] == "claim_boundary" for x in result["blindspots"])
    assert len(result["questions"]) == 2


def test_missing_evidence_is_not_treated_as_disproof():
    data = packet()
    data["claims"][0]["references"] = []
    result = analyze_document(data)
    assert result["claims"][0]["evidence_status"] == "no_references"
    assert "no_located_evidence" in result["claims"][0]["limits"]
    assert result["blindspots"][0]["basis"] == "no_references"
    assert all(c["semantic_support_verified"] is False for c in result["claims"])


@pytest.mark.parametrize("reference,status", [
    ({"source_id": "missing", "quote": "betere huiswerkcijfers"}, "unknown_source"),
    ({"source_id": "paper", "quote": "niet bestaande bronpassage"}, "quote_not_found"),
])
def test_bad_reference_is_visible_not_silently_accepted(reference, status):
    data = packet()
    data["claims"][0]["references"] = [reference]
    result = analyze_document(data)
    assert result["claims"][0]["evidence_status"] == "invalid_reference"
    assert result["claims"][0]["references"][0]["status"] == status
    assert result["blindspots"][0]["basis"] == "invalid_reference"


def test_gap_is_proposal_even_when_anchor_is_found():
    result = analyze_document(packet())
    gap = next(x for x in result["blindspots"] if x["id"] == "gap1")
    assert gap["status"] == "candidate_not_established"
    assert gap["anchor_status"] == "located_not_interpreted"
    assert result["questions"][-1]["status"] == "suggested_not_validated"


@pytest.mark.parametrize("modify", [
    lambda p: p["sources"].append(p["sources"][0].copy()),
    lambda p: p["claims"][0].update({"claim_type": "certain"}),
    lambda p: p["gaps"][0]["anchors"][0].update({"quote": ""}),
])
def test_invalid_packet_rejected_before_reporting(modify):
    data = packet()
    modify(data)
    with pytest.raises(ValueError):
        analyze_document(data)


class FakeBALLM:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def call(self, system_prompt, user_prompt, max_tokens, temperature):
        self.calls.append((system_prompt, user_prompt, max_tokens, temperature))
        return self.response


def test_ballm_proposes_specific_questions_without_evidence_promotion():
    fake = FakeBALLM(json.dumps({
        "gaps": [{
            "id": "ballm1", "description": "Onbekend of toetsen later standhouden.",
            "why_it_matters": "De conclusie is mogelijk te ruim.",
            "next_test": "Herhaal de meting na vier weken zonder hulpmiddel.",
            "anchors": [],
        }]
    }))
    result = analyze_document(packet(), proposer=BALLMDocumentProposer(fake))
    assert result["status"] == "complete"
    assert result["steps"][4]["status"] == "completed_unverified"
    proposal = next(g for g in result["blindspots"] if g["id"] == "ballm1")
    assert proposal["status"] == "candidate_not_established"
    assert result["claims"][0]["semantic_support_verified"] is False
    assert len(fake.calls) == 1
    assert "source" in fake.calls[0][1]


def test_failed_ballm_is_reported_partial_not_successful():
    fake = FakeBALLM('{"BLUF": "fallback"}')
    result = analyze_document(packet(), proposer=BALLMDocumentProposer(fake))
    assert result["status"] == "partial"
    assert result["proposal_error"]
    assert result["steps"][4]["status"] == "failed"
    assert result["claims"][0]["evidence_status"] == "quote_anchored_not_verified"


def test_duplicate_proposal_id_is_not_silently_merged():
    data = packet()
    def proposer(question, sources, claims):
        return [{
            "id": "gap1", "description": "Een tweede gap.",
            "why_it_matters": "Onbekend.",
            "next_test": "Wat ontbreekt?"
        }]
    with pytest.raises(ValueError, match="duplicate gap IDs"):
        analyze_document(data, proposer=proposer)


def test_offline_document_cli_keeps_osint_cli_independent(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    inp = tmp_path / "input.json"
    out = tmp_path / "nested" / "out.json"
    inp.write_text(json.dumps(packet()), encoding="utf8")
    r = CliRunner().invoke(cli, ["analyze-document", "--input", str(inp), "--out", str(out)])
    assert r.exit_code == 0, r.output
    result = json.loads(out.read_text(encoding="utf8"))
    assert result["schema"] == "ngbse.document-blindspot.v1"
    assert result["status"] == "complete"
    # The legacy CLI command still exists, unmodified.
    assert "run" in cli.commands and "ballm-analyze" in cli.commands


def test_cli_does_not_call_remote_model_without_explicit_provider(tmp_path, monkeypatch):
    for var in ["OPENAI_API_KEY", "AZURE_OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY", "COHERE_API_KEY"]:
        monkeypatch.delenv(var, raising=False)
    inp = tmp_path / "input.json"
    inp.write_text(json.dumps(packet()))
    out = tmp_path / "result.json"
    r = CliRunner().invoke(cli, ["analyze-document", "--input", str(inp), "--out", str(out), "--ballm"])
    assert r.exit_code != 0
    assert not out.exists()
    assert "no API call was made" in r.output
