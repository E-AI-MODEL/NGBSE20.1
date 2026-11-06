"""Two-turn ordinary-chat baseline, matched to the evidence produced by NGBSE.

The ordinary chat receives identical initial question and then the actual
experimental observations from the evidence cycle. It does NOT receive
NGBSE's own conclusion, analysis, or proposed verdict.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any

MODEL = "gpt-4.1-mini"
SYSTEM = (
    "Je bent een onderzoeker. Wees precies: een ontbrekende bron is geen "
    "bewijs van afwezigheid. Noem meetresultaten en open vragen; trek niet "
    "meer conclusies dan de gegevens rechtvaardigen. Antwoord in het Nederlands."
)
MAX_USD = 0.25
MAX_OUTPUT_TOKENS = 1300
# Conservative input/output cost proxies; not a billing guarantee.
INPUT_PER_M = 3.0
OUTPUT_PER_M = 12.0


def _hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def _reserve(messages: list[dict[str, str]]) -> float:
    chars = sum(len(m["content"]) for m in messages)
    if chars > 16_000:
        raise ValueError("Input exceeds bounded study limit")
    return 1.5 * ((chars / 2) * INPUT_PER_M + MAX_OUTPUT_TOKENS * OUTPUT_PER_M) / 1_000_000


def compare_chat(cycle: dict[str, Any], client: Any, output: Path) -> dict[str, Any]:
    if output.exists():
        raise ValueError("Refusing to repeat possibly paid model calls")
    if cycle.get("case_id") != "distutils-312-context":
        raise ValueError("Wrong test case")
    assert len(cycle["execution_receipts"]) == 3
    output.mkdir(parents=True)
    events = output / "chat_provider_events.jsonl"
    messages = [
        {"role": "developer", "content": SYSTEM},
        {"role": "user", "content": (
            "Onderzoeksvraag: " + cycle["initial_case"]["question"] +
            "\nTe onderzoeken uitspraak: " + cycle["initial_case"]["claims"][0]["text"] +
            "\nEr zijn nog geen testresultaten of aangeleverde bronnen. "
            "Welke eerstvolgende, toetsbare onderzoeksactie stel je voor? "
            "Noem ook wat een eventuele uitkomst wel en niet bewijst."
        )},
    ]
    # Use the complete, unmodified receipts. Omitting the executed command
    # would deprive the ordinary chat of information available to NGBSE.
    observations = cycle["execution_receipts"]
    total_reserved = 0.0
    spent_proxy = 0.0
    answer1 = None
    last_response = None
    for phase in (1, 2):
        if phase == 2:
            messages.append({"role": "assistant", "content": answer1 or ""})
            messages.append({"role": "user", "content": (
                "Hier zijn de daadwerkelijke testresultaten en opgehaalde "
                "bronpassages. Beoordeel nu de absolute bewering. "
                "Beschrijf precies welke bevindingen haar tegenspreken, "
                "welke stappen werkelijk zijn uitgevoerd en welke "
                "onzekerheden overblijven. Verwijs naar action_id's, "
                "maar verzin geen extra verificatie.\n" +
                json.dumps(observations, ensure_ascii=False)
            )})
        reservation = _reserve(messages)
        if total_reserved + reservation > MAX_USD:
            raise RuntimeError("BUDGET_STOP: no further provider calls")
        total_reserved += reservation
        with events.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps({
                "kind": "request_start", "phase": phase, "model": MODEL,
                "messages": messages, "messages_sha256": _hash(messages),
            }, ensure_ascii=False) + "\n")
        try:
            response = client.responses.create(
                model=MODEL, input=messages, max_output_tokens=MAX_OUTPUT_TOKENS,
                temperature=0.4, store=False,
            )
        except Exception as exc:
            with events.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps({
                    "kind": "request_error", "phase": phase,
                    "error_type": type(exc).__name__, "no_retry": True,
                }) + "\n")
            raise
        text = response.output_text or ""
        usage = response.usage.model_dump() if response.usage else {}
        spent_proxy += (
            usage.get("input_tokens", 0) * INPUT_PER_M +
            usage.get("output_tokens", 0) * OUTPUT_PER_M
        ) / 1_000_000
        last_response = {
            "phase": phase, "model_returned": response.model,
            "response_status": response.status, "response_id": response.id,
            "usage": usage, "text": text,
        }
        with events.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps({
                "kind": "response", **last_response
            }, ensure_ascii=False) + "\n")
        if response.status != "completed" or not text.strip():
            raise RuntimeError(
                f"Model answer incomplete or empty in phase {phase}; "
                "not a valid completed baseline"
            )
        if phase == 1:
            answer1 = text
        else:
            answer2 = text
    result = {
        "case_id": cycle["case_id"], "model_requested": MODEL,
        "provider_calls": 2, "initial_research_plan": answer1,
        "revised_answer_after_identical_evidence": answer2,
        "experimental_execution_by_chat": False,
        "same_receipts_as_ngbse": True,
        "actual_qualitative_review_completed": False,
        "estimated_cost_proxy_usd": round(spent_proxy, 6),
        "reservation_usd": round(total_reserved, 6),
        "budget_cap_usd": MAX_USD,
        "last_response": last_response,
        "evidence_sha256": _hash(observations),
    }
    (output / "chat_baseline.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cycle", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("NO_PROVIDER_KEY: zero model requests")
    from openai import OpenAI
    cycle = json.loads(args.cycle.read_text(encoding="utf-8"))
    result = compare_chat(cycle, OpenAI(timeout=75, max_retries=0), args.output)
    print(json.dumps({
        "case_id": result["case_id"],
        "calls": result["provider_calls"],
        "estimated_cost_proxy_usd": result["estimated_cost_proxy_usd"],
        "status": "provider_completed; independent evaluation pending",
    }), flush=True)


if __name__ == "__main__":
    main()
