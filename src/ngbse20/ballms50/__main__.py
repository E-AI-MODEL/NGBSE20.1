"""Offline CLI: python -m ngbse20.ballms50 case.json --out result.json"""
import argparse
import json
from pathlib import Path
import sys
from .engine import InputError, analyze


def main() -> int:
    parser = argparse.ArgumentParser(description="BALLMS 50 offline research analysis")
    parser.add_argument("case", help="Research case JSON")
    parser.add_argument("--out", required=True, help="Output JSON file")
    parser.add_argument("--question-budget", type=int, default=12)
    args = parser.parse_args()
    try:
        case = json.loads(Path(args.case).read_text(encoding="utf-8"))
        result = analyze(case, question_budget=args.question_budget)
        Path(args.out).write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    except (OSError, ValueError, InputError) as exc:
        print(f"BALLMS 50: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"analysis_status": result["analysis_status"], "gaps": len(result["gaps"]),
                      "selected_questions": len(result["selected_questions"]), "out": args.out}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
