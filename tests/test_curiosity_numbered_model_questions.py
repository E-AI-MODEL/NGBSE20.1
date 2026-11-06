"""Regressions for real model responses lost to numbered-line parsing.

The November 2026 Promptfoo run received six genuine model responses, all
three-line numbered lists. The old parser silently dropped every question.
"""
from ngbse20.ballm.curiosity_generator import CuriosityGenerationEngine


class FixedLLM:
    def __init__(self, text):
        self.text = text
        self.calls = 0

    def call(self, *_args, **_kwargs):
        self.calls += 1
        return self.text


def _engine(text):
    return CuriosityGenerationEngine(FixedLLM(text))


def test_numbered_lines_are_accepted_as_questions():
    engine = _engine(
        "1. How might we check source independence?\n"
        "2. What if a counterexample disproves the claim?\n"
        "3) Why does this result change across time?"
    )
    got = engine._parse_llm_curiosity_questions(engine.llm_client.text)
    assert len(got) == 3
    assert got[0]["question"] == "How might we check source independence?"
    assert got[1]["question"] == "What if a counterexample disproves the claim?"
    assert got[2]["question"] == "Why does this result change across time?"


def test_bullets_and_original_plain_lines_still_work():
    engine = _engine(
        "- How do we distinguish measurement error?\n"
        "* What are the independent sources?\n"
        "How might we test an alternative?"
    )
    got = engine._parse_llm_curiosity_questions(engine.llm_client.text)
    assert len(got) == 3
    assert got[0]["question"] == "How do we distinguish measurement error?"
    assert got[2]["question"] == "How might we test an alternative?"


def test_non_questions_are_not_accepted():
    engine = _engine(
        "Summary: these results are promising.\n"
        "1. Summary: not a research question.\n"
        "2. How might we test this independently?"
    )
    got = engine._parse_llm_curiosity_questions(engine.llm_client.text)
    assert [q["question"] for q in got] == ["How might we test this independently?"]


def test_question_limit_remains_three():
    engine = _engine("\n".join(
        f"{i}. How might we test unknown {i}?" for i in range(1, 7)
    ))
    got = engine._parse_llm_curiosity_questions(engine.llm_client.text)
    assert len(got) == 3


def test_public_method_retains_numbered_model_questions_under_small_budget():
    model = FixedLLM(
        "1. How might we verify source A?\n"
        "2. What if a third source contradicts A?\n"
        "3. Why does the measurement change over time?"
    )
    questions = CuriosityGenerationEngine(model).generate_curiosity_questions(
        [], {
            "coverage": {"ratios": {}, "imbalance": 0},
            "recency": {"spike": False},
            "confidence": {"n": 0},
        }
    )
    assert model.calls == 1
    selected = [q for q in questions if q["type"] == "llm_generated"]
    assert len(selected) == 3


def test_crowded_question_selection_remains_a_separate_limit():
    model = FixedLLM("1. How might we verify a missing alternative?")
    questions = CuriosityGenerationEngine(model).generate_curiosity_questions(
        [], {
            "coverage": {
                "ratios": {f"rare-{i}": 0.01 for i in range(12)},
                "imbalance": 0.9, "max_category": "common",
            },
            "recency": {"spike": True},
            "confidence": {"n": 1, "risky_assets": ["item"]},
        }
    )
    # This test records a distinct known problem, NOT a claim it was fixed.
    assert model.calls == 1
    assert len(questions) == 10
    assert not [q for q in questions if q["type"] == "llm_generated"]
