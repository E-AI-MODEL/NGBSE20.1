"""Generate 18 actual-output cases for Promptfoo without inventing outputs."""
from __future__ import annotations

import json
from pathlib import Path


def generate_tests(config=None):
    suite = json.loads((Path(__file__).parent / "cases.json").read_text(encoding="utf-8"))
    tests = []
    for case in suite["cases"]:
        for arm in suite["arms"]:
            tests.append({
                "description": f"Real provider output: {case['id']} / {arm}",
                "vars": {"input_json": json.dumps({"case_id": case["id"], "arm": arm})},
                "assert": [
                    {"type": "is-json"},
                    {"type": "javascript", "value": (
                        "const x=JSON.parse(output);"
                        f"if(x.case_id !== '{case['id']}' || x.arm !== '{arm}') return false;"
                        "if(!x.model_used || !Array.isArray(x.questions)) return false;"
                        "if(x.questions.length<1 || x.questions.length>6) return false;"
                        "const q=x.questions.map(s=>String(s).trim().toLowerCase());"
                        "if(q.some(s=>s.length<12)) return false;"
                        "if(new Set(q).size!==q.length) return false;"
                        "if(x.arm==='ballms50') return x.model_status==='ok' && "
                        "x.trace_links.length===x.questions.length;"
                        "return true;"
                    )},
                ],
            })
    return tests
