"""Selection and epistemic regressions for the historical NGBSE BALLM engine.

These tests assert selection mechanics, not that any question is scientifically
useful. The six real responses are replayed separately without new model calls.
"""
import pytest

from ngbse20.ballm.curiosity_generator import CuriosityGenerationEngine


class FixedModel:
    def __init__(self, text=""):
        self.text = text
        self.calls = 0

    def call(self, *_args, **_kwargs):
        self.calls += 1
        return self.text


def question(kind, text, level="medium"):
    return {
        "type": kind, "question": text,
        "curiosity_level": level, "category": "research",
    }


def test_balanced_selection_keeps_a_model_question_in_first_ten():
    many_coverage = [
        question("coverage_gap", f"How might source {i} affect the conclusion?")
        for i in range(15)
    ]
    candidate_list = many_coverage + [
        question("recency_gap", "What happened after the reported change?"),
        question("confidence_gap", "Which measurements are independently checked?"),
        question("llm_generated", "What if a counterexample changes the explanation?", "high"),
        question("productive_failure", "How could a failed trial become evidence?"),
    ]
    report = CuriosityGenerationEngine._select_curiosity_questions(candidate_list)
    selected = report["selected_questions"]
    assert len(selected) == 10
    assert len({q["type"] for q in selected}) == 5
    assert any(q["type"] == "llm_generated" for q in selected[:5])
    assert report["candidate_count"] == len(candidate_list)
    assert len(report["excluded_questions"]) == len(candidate_list) - 10
    assert all(x["reason"] == "question_budget" for x in report["excluded_questions"])
    assert report["selection_policy"] == "balanced_families_on_overflow"


def test_high_before_medium_within_family_without_promising_quality():
    candidates = [
        question("coverage_gap", "Question from coverage, low.", "low"),
        question("coverage_gap", "Question from coverage, high.", "high"),
        question("llm_generated", "Model question A.", "medium"),
        question("llm_generated", "Model question B.", "high"),
        question("confidence_gap", "Confidence question.", "medium"),
        question("recency_gap", "Recency question.", "high"),
    ]
    selected = CuriosityGenerationEngine._select_curiosity_questions(candidates, limit=4)[
        "selected_questions"
    ]
    assert [q["question"] for q in selected] == [
        "Question from coverage, high.",
        "Model question B.",
        "Confidence question.",
        "Recency question.",
    ]


def test_short_lists_keep_previous_order_and_full_dict_payloads():
    candidates = [
        question("coverage_gap", "Coverage question.", "low"),
        question("llm_generated", "Model question.", "high"),
        question("confidence_gap", "Confidence question.", "medium"),
    ]
    report = CuriosityGenerationEngine._select_curiosity_questions(candidates, limit=5)
    assert report["selected_questions"] == candidates
    assert report["excluded_questions"] == []
    assert report["candidate_count"] == 3


def test_exact_text_duplicates_are_recorded_and_not_selected():
    candidates = [
        question("coverage_gap", "Which source supports the claim?"),
        question("llm_generated", " which  source supports the claim? ", "high"),
        question("llm_generated", "What if another source contradicts the claim?"),
    ]
    report = CuriosityGenerationEngine._select_curiosity_questions(candidates, limit=10)
    assert len(report["selected_questions"]) == 2
    assert len(report["excluded_questions"]) == 1
    assert report["excluded_questions"][0]["reason"] == "duplicate_question"
    assert report["selected_questions"][0] is candidates[0]
    # Preserve candidates: no mutation of the original dicts.
    assert candidates[1]["question"] == " which  source supports the claim? "


def test_empty_and_invalid_questions_cannot_use_budget():
    report = CuriosityGenerationEngine._select_curiosity_questions([
        question("coverage_gap", ""),
        question("confidence_gap", "    "),
        question("llm_generated", "How might we falsify the account?"),
    ], limit=10)
    assert len(report["selected_questions"]) == 1
    assert [x["reason"] for x in report["excluded_questions"]] == [
        "empty_or_invalid_question", "empty_or_invalid_question"
    ]


@pytest.mark.parametrize("limit", [0, -1, True, 2.5])
def test_limit_requires_positive_integer(limit):
    with pytest.raises(ValueError):
        CuriosityGenerationEngine._select_curiosity_questions([], limit=limit)


def test_no_reported_gap_does_not_invent_security_or_data_quality_failures():
    model = FixedModel("")
    report = CuriosityGenerationEngine(model).generate_curiosity_questions_with_trace(
        [], {
            "coverage": {"ratios": {}, "imbalance": 0},
            "confidence": {"n": 0},
            "recency": {"spike": False, "detail": {}},
        },
    )
    assert model.calls == 1
    assert report["selected_questions"] == []
    assert report["excluded_questions"] == []


def test_valid_signals_still_produce_rule_questions_without_a_model():
    class BrokenModel:
        def call(self, *_args, **_kwargs):
            raise RuntimeError("Provider offline")

    engine = CuriosityGenerationEngine(BrokenModel())
    result = engine.generate_curiosity_questions(
        [], {
            "coverage": {"imbalance": 0.8, "max_category": "single source"},
            "recency": {"spike": False},
            "confidence": {"n": 1, "risky_assets": ["sensor"]},
        }
    )
    assert result
    assert all(q["type"] != "llm_generated" for q in result)
    assert any(q["type"] == "coverage_gap" for q in result)
    assert any(q["type"] == "confidence_gap" for q in result)


def test_budgeted_selection_is_deterministic_with_multiple_model_questions():
    candidates = [
        question("coverage_gap", f"Test missing source {i}?")
        for i in range(12)
    ] + [
        question("llm_generated", "Could other evidence weaken the claim?", "high"),
        question("llm_generated", "Can a negative control distinguish causes?", "high"),
        question("productive_failure", "What does the failed search rule out?"),
    ]
    report_a = CuriosityGenerationEngine._select_curiosity_questions(candidates, limit=6)
    report_b = CuriosityGenerationEngine._select_curiosity_questions(candidates, limit=6)
    assert report_a == report_b
    assert len(report_a["selected_questions"]) == 6
    assert any(q["type"] == "llm_generated" for q in report_a["selected_questions"])
    assert len(report_a["excluded_questions"]) == len(candidates) - 6
