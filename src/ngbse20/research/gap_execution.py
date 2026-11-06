"""One real, bounded gap-to-evidence experiment on top of BALLMS 50.

The first research action is a fixed Python 3.12 A/B import probe.
It also retrieves an official document from one exact allowlisted URL.
This is a *single-case experimental adapter*, not a general autonomous agent.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any, Callable
from urllib.request import Request, urlopen

from ngbse20.ballms50 import analyze

DOCUMENT_URL = "https://docs.python.org/3.12/whatsnew/3.12.html"
CASE_ID = "distutils-312-context"
CLAIM = "Python 3.12 kan in geen enkele omgeving distutils importeren."
MAX_BYTES = 2_000_000


class _Text(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.chunks: list[str] = []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.skip += 1

    def handle_endtag(self, tag):
        if tag in ("script", "style") and self.skip:
            self.skip -= 1

    def handle_data(self, text):
        if not self.skip:
            self.chunks.append(text)


def make_case() -> dict[str, Any]:
    return {
        "study_id": CASE_ID,
        "question": "Geldt de verwijdering van distutils voor elke Python 3.12-omgeving?",
        "sources": [],
        "claims": [{"id": "absolute", "text": CLAIM, "references": []}],
        "unknowns": [
            {"id": "environments", "question": "Werkt een import anders met en zonder geïnstalleerde setuptools?"}
        ],
    }


def make_actions() -> list[dict[str, Any]]:
    return [
        {
            "id": "A1",
            "kind": "python_import_test",
            "condition": "isolated_no_site",
            "command": [sys.executable, "-I", "-S", "-c", "import distutils"],
            "expected_interpretation": "Een mislukte import bewijst alleen wat in deze geïsoleerde omgeving gebeurt.",
        },
        {
            "id": "A2",
            "kind": "python_import_test",
            "condition": "installed_setuptools",
            "command": [
                sys.executable, "-I", "-c",
                "import setuptools; import distutils; print(distutils.__file__)",
            ],
            "expected_interpretation": "Een geslaagde import is een tegenvoorbeeld voor de absolute bewering.",
        },
        {
            "id": "A3",
            "kind": "official_document_retrieval",
            "url": DOCUMENT_URL,
            "expected_interpretation": "De officiële documentatie helpt de reikwijdte te verklaren, geen tweede uitvoering.",
        },
    ]


def _subprocess(cmd, timeout):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False)


def _fetch(url, timeout):
    if url != DOCUMENT_URL:
        raise ValueError("URL is not on the single-source allowlist")
    with urlopen(Request(url, headers={"User-Agent": "NGBSE-Research-Pilot/0.1"}), timeout=timeout) as response:
        data = response.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            raise ValueError("response exceeds size cap")
        return {
            "status_code": response.status,
            "bytes": data,
            "final_url": response.geturl(),
        }


def perform_actions(
    *, run_command: Callable[..., Any] = _subprocess,
    fetch: Callable[..., Any] = _fetch,
    python_version: tuple[int, int] | None = None,
) -> list[dict[str, Any]]:
    """Execute two fixed commands and one tightly bounded remote retrieval.

    All actions are recorded, including failures. A missing receipt never
    becomes negative evidence. No arbitrary shell input is accepted.
    """
    python_version = python_version or sys.version_info[:2]
    if python_version != (3, 12):
        raise RuntimeError("This exact experiment requires Python 3.12")
    receipts = []
    for action in make_actions():
        if action["kind"] == "python_import_test":
            try:
                result = run_command(action["command"], timeout=12)
                receipts.append({
                    "action_id": action["id"], "kind": "python_import_test",
                    "condition": action["condition"], "executed_by_runner": True,
                    "status": "completed", "returncode": result.returncode,
                    "stdout": result.stdout[-2000:], "stderr": result.stderr[-2000:],
                    "python_version": ".".join(map(str, python_version)),
                    "command": action["command"], "test_environment_only": True,
                })
            except (OSError, subprocess.TimeoutExpired) as exc:
                receipts.append({
                    "action_id": action["id"], "kind": "python_import_test",
                    "condition": action["condition"], "executed_by_runner": False,
                    "status": "error", "error_type": type(exc).__name__,
                })
        else:
            try:
                response = fetch(action["url"], timeout=12)
                if response["final_url"] != DOCUMENT_URL:
                    raise ValueError("redirected outside exact document allowlist")
                raw = response["bytes"]
                if not isinstance(raw, bytes) or len(raw) > MAX_BYTES:
                    raise ValueError("invalid source bytes")
                parsed = _Text()
                parsed.feed(raw.decode("utf-8", errors="replace"))
                normalized = re.sub(r"\s+", " ", " ".join(parsed.chunks)).strip()
                snippets = []
                for needle in ("distutils package", "setuptools package", "Setuptools package", "Setuptools"):
                    position = normalized.casefold().find(needle.casefold())
                    if position >= 0:
                        snippet = normalized[max(0, position - 110):position + 320]
                        if snippet not in snippets:
                            snippets.append(snippet)
                receipts.append({
                    "action_id": action["id"], "kind": "official_document_retrieval",
                    "status": "completed", "executed_by_runner": True,
                    "url": action["url"], "http_status": response["status_code"],
                    "raw_sha256": sha256(raw).hexdigest(),
                    "raw_size": len(raw), "extracted_snippets": snippets[:4],
                    "source_family": "python-documentation", "meaning_verified": False,
                })
            except (OSError, ValueError, TimeoutError) as exc:
                receipts.append({
                    "action_id": action["id"], "kind": "official_document_retrieval",
                    "status": "error", "executed_by_runner": False,
                    "url": action["url"], "error_type": type(exc).__name__,
                })
    return receipts


def _source_from_probe(receipt: dict[str, Any]) -> dict[str, Any]:
    text = (
        f"Action {receipt['action_id']} in {receipt['condition']} environment. "
        f"returncode={receipt['returncode']}. "
        f"stdout={receipt['stdout']}. stderr={receipt['stderr']}."
    )
    return {
        "id": "probe-" + receipt["action_id"],
        "origin_id": "executed:" + receipt["action_id"],
        "type": "executed_probe", "text": text,
    }


def reconcile(receipts: list[dict[str, Any]]) -> dict[str, Any]:
    """Make only the logical conclusion warranted by the two observed runs."""
    by_id = {r["action_id"]: r for r in receipts}
    a, b = by_id.get("A1", {}), by_id.get("A2", {})
    if not (a.get("status") == "completed" and b.get("status") == "completed"):
        return {
            "status": "not_established", "statement": "Niet beide proefcondities zijn uitgevoerd.",
            "evidence_ids": [], "remaining_unknown": "Importgedrag is nog niet vastgesteld.",
        }
    if a["returncode"] != 0 and b["returncode"] == 0 and "_distutils" in b["stdout"]:
        return {
            "status": "absolute_claim_refuted_in_test",
            "statement": (
                "De absolute bewering is voor de geteste Python 3.12-omgeving weerlegd: "
                "zonder site-packages mislukt de import, met setuptools lukt hij. "
                "Dit bewijst niets over andere omgevingen of alle pakketversies."
            ),
            "evidence_ids": ["probe-A1", "probe-A2"],
            "remaining_unknown": "Andere installaties, distributies en platformen zijn niet getest.",
        }
    return {
        "status": "inconclusive",
        "statement": "De twee resultaten ondersteunen de vooraf gedefinieerde weerlegging niet.",
        "evidence_ids": ["probe-A1", "probe-A2"],
        "remaining_unknown": "Onderzoek de omgeving en bron van de import.",
    }


def execute_cycle(
    *, run_command: Callable[..., Any] = _subprocess,
    fetch: Callable[..., Any] = _fetch,
    python_version: tuple[int, int] | None = None,
) -> dict[str, Any]:
    """BALLMS 50 gap -> planned action -> actual evidence -> renewed analysis."""
    initial_case = make_case()
    before = analyze(initial_case, question_budget=5)
    required_gaps = {"missing_evidence", "no_sources", "open_question"}
    present_gaps = {g["kind"] for g in before["gaps"]}
    if not required_gaps.issubset(present_gaps):
        raise RuntimeError("BALLMS 50 failed to identify the expected gaps")
    receipts = perform_actions(
        run_command=run_command, fetch=fetch, python_version=python_version
    )
    after_case = make_case()
    for receipt in receipts:
        if receipt["kind"] == "python_import_test" and receipt["status"] == "completed":
            after_case["sources"].append(_source_from_probe(receipt))
        if receipt["kind"] == "official_document_retrieval" and receipt["status"] == "completed":
            snippets = receipt["extracted_snippets"]
            if snippets:
                after_case["sources"].append({
                    "id": "official-document", "origin_id": receipt["source_family"],
                    "type": "official_document", "text": "\n".join(snippets),
                })
    # Raw execution receipts are held outside BALLMS 50. Its probe_results
    # are *reported only* and must never be called verified execution.
    after = analyze(after_case, question_budget=5)
    verdict = reconcile(receipts)
    return {
        "case_id": CASE_ID,
        "initial_case": initial_case,
        "initial_analysis": before,
        "planned_actions": make_actions(),
        "execution_receipts": receipts,
        "after_case": after_case,
        "after_analysis": after,
        "verdict": verdict,
        "trace": [
            {"stage": "gap", "status": "generated_by_ballms50",
             "gap_ids": [g["id"] for g in before["gaps"]]},
            {"stage": "test", "status": "predefined_bounded_actions"},
            {"stage": "execution", "status": "completed" if all(
                r["status"] == "completed" for r in receipts
            ) else "partial", "actually_executed": sum(
                bool(r["executed_by_runner"]) for r in receipts
            )},
            {"stage": "new_evidence", "status": "received",
             "source_ids": [s["id"] for s in after_case["sources"]]},
            {"stage": "reanalysis", "status": after["analysis_status"],
             "note": "BALLMS does not verify semantic support from quotations"},
            {"stage": "revised_conclusion", "status": verdict["status"]},
        ],
        "method_limits": [
            "single preselected case; actions are scripted, not autonomously selected",
            "real subprocess receipts are from a bounded test environment",
            "source retrieval is not a semantic evidence verifier",
            "a quote match and a source fingerprint alone do not establish truth",
            "no observed advantage over an ordinary AI chat without matched comparison",
        ],
    }


def save_cycle(cycle: dict[str, Any], directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    for name, value in [
        ("before.json", cycle["initial_analysis"]),
        ("actions.json", cycle["planned_actions"]),
        ("receipts.json", cycle["execution_receipts"]),
        ("after.json", cycle["after_analysis"]),
        ("cycle.json", cycle),
    ]:
        (directory / name).write_text(
            json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )


def main() -> None:
    """Run the tightly scoped evidence cycle; export inspectable receipts."""
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("research-artifacts/gap-cycle"))
    args = parser.parse_args()
    cycle = execute_cycle()
    save_cycle(cycle, args.output)
    print(json.dumps({
        "study_id": CASE_ID,
        "initial_gaps": len(cycle["initial_analysis"]["gaps"]),
        "actual_actions_completed": sum(
            1 for item in cycle["execution_receipts"]
            if item["status"] == "completed"
        ),
        "document_retrieval_status": cycle["execution_receipts"][2]["status"],
        "new_sources": len(cycle["after_case"]["sources"]),
        "verdict_status": cycle["verdict"]["status"],
        "remaining_unknown": cycle["verdict"]["remaining_unknown"],
        "source_execution": "real_python_312_and_official_document",
        "not_yet_comparative": True,
    }, ensure_ascii=False), flush=True)
    if cycle["verdict"]["status"] != "absolute_claim_refuted_in_test":
        raise SystemExit("Pilot inconclusive; cannot claim a tested result")


if __name__ == "__main__":
    main()
