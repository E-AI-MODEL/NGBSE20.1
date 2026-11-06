#!/usr/bin/env python3
"""Replay real November 2026 numbered NGBSE model answers, without new API calls."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from ngbse20.ballm.curiosity_generator import CuriosityGenerationEngine  # noqa: E402


class RecordedModel:
    def __init__(self, response):
        self.response = response
        self.calls = 0

    def call(self, *_args, **_kwargs):
        self.calls += 1
        return self.response


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--events", type=Path, required=True)
    parser.add_argument("--answers", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    events = [json.loads(row) for row in args.events.read_text(encoding="utf-8").splitlines()]
    before = json.loads(args.answers.read_text(encoding="utf-8"))
    old = {x["case_id"]: x for x in before if x["arm"] == "legacy"}
    fixture = json.loads((ROOT / "research/ngbse_quality/cases.json").read_text(encoding="utf-8"))
    by_id = {x["id"]: x for x in fixture["cases"]}
    responses = [x for x in events if x.get("kind") == "response" and x.get("arm") == "legacy"]
    assert len(responses) == 6, f"Expected exactly six recorded model responses, got {len(responses)}"
    assert len(old) == 6 and len(by_id) == 6
    rows = []
    for event in sorted(responses, key=lambda x: x["case"]):
        cid = event["case"]
        assert cid in old and cid in by_id
        raw = event["answer"]
        model = RecordedModel(raw)
        engine = CuriosityGenerationEngine(model)
        parsed = engine._parse_llm_curiosity_questions(raw)
        selected = engine.generate_curiosity_questions([], by_id[cid]["legacy"])
        model_selected = [x["question"] for x in selected if x["type"] == "llm_generated"]
        original_model_selected = sum(
            k == "llm_generated" for k in old[cid].get("question_types", [])
        )
        assert model.calls == 1
        assert len(parsed) == 3, f"{cid}: expected 3 numbered questions, got {len(parsed)}"
        assert original_model_selected == 0, "The original artifact must remain unchanged"
        rows.append({
            "case_id": cid,
            "model_questions_in_original_response": 3,
            "model_questions_recovered_by_parser": len(parsed),
            "original_model_questions_in_first_six": original_model_selected,
            "repaired_model_questions_in_first_six": sum(
                x in [q["question"] for q in selected[:6]] for x in model_selected
            ),
            "repaired_model_questions_in_full_ten": len(model_selected),
            "original_selected_question_count": len(old[cid]["questions"]),
            "repaired_selected_question_count": len(selected),
            "recovered_model_texts": [q["question"] for q in parsed],
            "selected_question_types": [q["type"] for q in selected],
        })
    result = {
        "source_model_calls_reused": len(responses),
        "new_provider_calls": 0,
        "total_real_numbered_model_questions": sum(x["model_questions_in_original_response"] for x in rows),
        "parser_recovered_total": sum(x["model_questions_recovered_by_parser"] for x in rows),
        "old_model_questions_selected_first_six": 0,
        "new_model_questions_selected_first_six": sum(x["repaired_model_questions_in_first_six"] for x in rows),
        "new_model_questions_selected_full_ten": sum(x["repaired_model_questions_in_full_ten"] for x in rows),
        "cases": rows,
        "note": "Parser repair only. Scoring question content and the separate selection truncation remain open.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print("REPLAY "+json.dumps({k:v for k,v in result.items() if k!="cases"}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
