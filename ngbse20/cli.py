"""CLI entrypoint for NGBSE 20.1."""
import json
import argparse
from .runtime.orchestrator import run_pipeline


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["demo"])
    ap.add_argument("--rules", dest="rules_path", default=None)
    ap.add_argument("--seeds", dest="seeds_path", default=None)
    ap.add_argument("--metrics", dest="metrics_json", default='{}')
    ap.add_argument("--outdir", default='out', help="Output directory")
    ap.add_argument("--allowlist", default='*', help="Comma-separated allowed domains")
    args = ap.parse_args()

    rules = []
    if args.rules_path:
        with open(args.rules_path, 'r', encoding='utf-8') as fp:
            rules = json.load(fp)

    seeds = []
    if args.seeds_path:
        with open(args.seeds_path, 'r', encoding='utf-8') as fp:
            for line in fp:
                if line.strip():
                    seeds.append(json.loads(line))

    try:
        metrics = json.loads(args.metrics_json)
    except Exception:
        metrics = {}

    config = {
        "output_dir": args.outdir,
        "allowlist": [d.strip() for d in args.allowlist.split(',')]
    }

    result = run_pipeline(seeds=seeds, rules=rules, metrics=metrics, config=config)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
