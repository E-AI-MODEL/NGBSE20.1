#!/usr/bin/env python3
"""Capped, source-pinned NGBSE three-arm question-quality pilot.

No source code is replaced. Real model calls use only fictional cases.
The old generator is invoked via its public method, BALLMS 50 via analyze().
A plain prompt is the comparison arm. This tests question outputs, not searches.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import random
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

MODEL = "gpt-4.1-mini"
ARMS = ("plain", "legacy", "ballms50")
MAX_OUTPUT = 850
MAX_USD = 0.50
# Conservative reservations, NOT a provider quote or reliable billing calculation.
INPUT_USD_PER_M = 3.00
OUTPUT_USD_PER_M = 12.00
SYSTEM = (
    "Je bent een zorgvuldige onderzoeker. Stel maximaal zes beknopte, "
    "toetsbare vervolgvragen. Scheid waarneming, bewering en ontbrekend bewijs. "
    "Maak geen vaststaande feiten van hypotheses. Noem waar mogelijk een "
    "onderscheidende toets of tegenvoorbeeld. Geen algemene opvulvragen."
)


def digest(obj):
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
    ).hexdigest()


def load_cases():
    path = ROOT / "research/ngbse_quality/cases.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["suite"] == "ngbse-quality-v1"
    assert len(data["cases"]) == 6
    assert data["arms"] == list(ARMS)
    assert data["question_budget"] == 6
    ids = [c["id"] for c in data["cases"]]
    assert len(set(ids)) == 6
    for case in data["cases"]:
        assert set(case) >= {"id", "title", "packet", "legacy", "expected_gap_kinds"}
        assert case["packet"]["study_id"] == case["id"]
        assert all(len(str(s.get("text", ""))) < 5000 for s in case["packet"]["sources"])
    return data


def json_object(raw):
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        raise ValueError("Model did not return the required JSON object") from None


def extract_questions(obj, *, max_questions=6):
    if not isinstance(obj, dict) or not isinstance(obj.get("questions"), list):
        raise ValueError("Model response must contain questions list")
    rows = []
    for item in obj["questions"][:max_questions]:
        text = item if isinstance(item, str) else item.get("question") if isinstance(item, dict) else None
        if isinstance(text, str) and text.strip():
            rows.append(text.strip())
    return rows


def conditions():
    data = load_cases()
    combinations = [(case, arm) for case in data["cases"] for arm in ARMS]
    random.Random(20261106).shuffle(combinations)
    return combinations


def reserve_cost(messages):
    chars = sum(len(str(m["content"])) for m in messages)
    if chars > 25000:
        raise ValueError("Input too long for capped trial")
    # Upper reservation: 1 token per ~2 characters and full output budget.
    return 1.5 * (
        (chars / 2.0) * INPUT_USD_PER_M + MAX_OUTPUT * OUTPUT_USD_PER_M
    ) / 1_000_000


def offline_preflight():
    from ngbse20.ballms50 import analyze

    data = load_cases()
    by_id = {case["id"]: case for case in data["cases"]}
    assert len(conditions()) == 18
    assert len({(c["id"], arm) for c, arm in conditions()}) == 18
    for case in data["cases"]:
        packet = case["packet"]
        result = analyze(packet, question_budget=6)
        assert result["analysis_status"] == "analysis_complete"
        assert result["investigation_status"] == "not_executed_by_engine"
        kinds = {g["kind"] for g in result["gaps"]}
        for wanted in case["expected_gap_kinds"]:
            assert wanted in kinds, (case["id"], wanted, kinds)
        if not case["expected_gap_kinds"]:
            assert not kinds, (case["id"], kinds)
        assert all(q["semantic_support"] == "NOT_EVALUATED" for q in result["questions"])
        assert len(result["selected_questions"]) <= 6
    assert all(by_id[c["id"]] == c for c, arm in conditions())
    print("PREFLIGHT_OK cases=6 arms=3 planned_provider_calls=18 no_model_calls=1", flush=True)


class ModelCalls:
    def __init__(self, client, events_path):
        self.client = client
        self.path = events_path
        self.received_cost = 0.0
        self.reserved_cost = 0.0
        self.calls = 0
        self.phase = ""

    def write(self, event):
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
            handle.flush()
            os.fsync(handle.fileno())

    def call(self, system, user, *, temperature=0.4, max_tokens=850):
        messages = [{"role": "developer", "content": system}, {"role": "user", "content": user}]
        reservation = reserve_cost(messages)
        if self.reserved_cost + reservation > MAX_USD:
            raise RuntimeError("BUDGET_STOP before next request")
        self.reserved_cost += reservation
        self.calls += 1
        meta = {
            "case": self.phase.split("/")[0], "arm": self.phase.split("/")[1],
            "request_index": self.calls, "messages_sha256": digest(messages),
            "messages": messages, "model_requested": MODEL,
        }
        self.write({"kind": "request_start", **meta})
        t0 = time.monotonic()
        try:
            response = self.client.responses.create(
                model=MODEL, input=messages, temperature=temperature,
                max_output_tokens=min(max_tokens, MAX_OUTPUT), store=False,
            )
            answer = response.output_text or ""
            usage = response.usage.model_dump() if response.usage else {}
            actual = (usage.get("input_tokens", 0) * INPUT_USD_PER_M +
                      usage.get("output_tokens", 0) * OUTPUT_USD_PER_M) / 1_000_000
            self.received_cost += actual
            self.write({
                "kind": "response", **meta, "model_returned": response.model,
                "response_id": response.id, "response_status": response.status,
                "answer": answer, "answer_sha256": hashlib.sha256(answer.encode()).hexdigest(),
                "usage": usage, "estimated_cost_upper_proxy": actual,
                "elapsed_seconds": round(time.monotonic() - t0, 3),
            })
            return answer
        except Exception as exc:
            self.write({
                "kind": "request_error", **meta,
                "error_type": type(exc).__name__,
                "error_text": "Provider call failed; no retry to avoid possible double charge",
            })
            raise


def run_arm(case, arm, calls):
    from ngbse20.ballm.curiosity_generator import CuriosityGenerationEngine
    from ngbse20.ballms50 import analyze

    packet = case["packet"]
    if arm == "plain":
        request = (
            "Onderzoeksvraag: " + packet.get("question", "") +
            "\nOnderzoeksdossier (synthetisch):\n" + json.dumps(packet, ensure_ascii=False) +
            '\nAntwoord uitsluitend als JSON: {"questions": ["vraag", "..."]}. '
            "Geef hoogstens zes vragen."
        )
        raw = calls.call(SYSTEM, request)
        questions = extract_questions(json_object(raw))
        return {
            "questions": questions, "trace_links": [],
            "analysis_status": "provider_response",
            "raw_model_response": raw,
            "model_used": True,
        }

    if arm == "legacy":
        class LiveClient:
            def call(self, system, prompt, max_tokens=300, temperature=0.4):
                return calls.call(system, prompt, temperature=temperature, max_tokens=max_tokens)
        generator = CuriosityGenerationEngine(LiveClient())
        response = generator.generate_curiosity_questions([], case["legacy"])
        return {
            "questions": [r["question"] for r in response[:6]],
            "question_types": [r["type"] for r in response[:6]],
            "analysis_status": "legacy_method",
            "model_used": True,
            "note": "Legacy function receives only historic summary features, not the full source dossier.",
        }

    if arm == "ballms50":
        def propose(payload):
            prompt = (
                "Voor deze onderzoekspunten mag je maximaal zes aanvullende "
                "onderzoeksvragen voorstellen. Elke vraag verwijst naar precies een "
                "bestaand gap_id. Voeg nooit een niet-bestaand ID toe.\n" +
                json.dumps(payload, ensure_ascii=False) +
                '\nGeef uitsluitend JSON in dit formaat: {"questions": '
                '[{"gap_id": "G-...", "question": "..."}]}.'
            )
            obj = json_object(calls.call(SYSTEM, prompt))
            return obj.get("questions", []) if isinstance(obj, dict) else []
        result = analyze(packet, question_budget=6, proposer=propose)
        by_id = {q["id"]: q for q in result["questions"]}
        chosen = [by_id[qid] for qid in result["selected_questions"]]
        return {
            "questions": [q["question"] for q in chosen],
            "trace_links": [
                {"gap_id": q["gap_id"], "question_id": q["id"], "kind": q["kind"],
                 "origin": q["origin"]} for q in chosen
            ],
            "analysis_status": result["analysis_status"],
            "model_status": next((e["status"] for e in result["trace"]
                                 if e["stage"] == "model_proposer"), None),
            "all_candidate_count": len(result["questions"]),
            "excluded_candidate_count": len(result["excluded_questions"]),
            "model_used": True,
        }

    raise ValueError("Unknown arm")


def write_review(out, rows):
    random.Random(20261107).shuffle(rows)
    mapping = {}
    with (out / "blind_review.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "anonymous_id", "case_id", "case_title", "research_question",
            "dossier_json", "questions_json", "grounded_specificity_0_2",
            "discriminating_test_0_2", "unsupported_premise_count",
            "duplicate_question_count", "useful_for_followup_0_2", "notes"
        ])
        for i, row in enumerate(rows):
            identity = f"V{i+1:02d}"
            mapping[identity] = {"case_id": row["case_id"], "arm": row["arm"]}
            writer.writerow([
                identity, row["case_id"], row["title"], row["question"],
                json.dumps(row["dossier"], ensure_ascii=False),
                json.dumps(row["questions"], ensure_ascii=False),
                "", "", "", "", "", ""
            ])
    (out / "PRIVATE_MAPPING.json").write_text(
        json.dumps(mapping, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--preflight", action="store_true")
    parser.add_argument("--output", default="research-artifacts/ngbse-quality-v1")
    opts = parser.parse_args()
    offline_preflight()
    if opts.preflight:
        return
    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("BLOCKED_NO_PROVIDER_KEY: zero model calls sent")
    from openai import OpenAI
    out = Path(opts.output)
    out.mkdir(parents=True, exist_ok=True)
    events = out / "provider_events.jsonl"
    if events.exists():
        raise SystemExit("BLOCKED_ALREADY_STARTED: refusing repeated paid requests")
    client = OpenAI(timeout=75, max_retries=0)
    calls = ModelCalls(client, events)
    answers = []
    failure = None
    cases = load_cases()
    for case, arm in conditions():
        calls.phase = f"{case['id']}/{arm}"
        try:
            result = run_arm(case, arm, calls)
            answers.append({
                "case_id": case["id"], "title": case["title"],
                "question": case["question"], "arm": arm,
                "dossier": case["packet"], **result,
            })
            print("RECEIVED case=%s arm=%s count=%d" %
                  (case["id"], arm, len(result["questions"])), flush=True)
        except Exception as exc:
            failure = {"case": case["id"], "arm": arm, "kind": type(exc).__name__}
            break
    review_rows = [a.copy() for a in answers if isinstance(a.get("questions"), list)]
    write_review(out, review_rows)
    summary = {
        "status": "PROVIDER_COMPLETED" if failure is None else "PARTIAL_OR_BLOCKED",
        "model_requested": MODEL, "suite": cases["suite"],
        "cases": len(cases["cases"]), "arms": list(ARMS),
        "planned_calls": 18, "attempted_calls": calls.calls,
        "received_outputs": len(answers),
        "estimated_cost_upper_proxy_usd": round(calls.received_cost, 6),
        "reserved_budget_usd": round(calls.reserved_cost, 6),
        "budget_cap_usd": MAX_USD, "failure": failure,
        "independent_human_review_completed": False,
        "no_quality_winner_claimed": True,
        "notes": [
            "The ordinary baseline and model proposer receive dossier/gap details.",
            "The old generator receives the historic feature summary as its API requires.",
            "Question quality and investigation outcomes are not established by call success.",
        ],
    }
    (out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2)+"\n")
    (out / "answers.json").write_text(json.dumps(answers, ensure_ascii=False, indent=2)+"\n")
    print("SUMMARY "+json.dumps(summary, ensure_ascii=False), flush=True)
    if failure:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
