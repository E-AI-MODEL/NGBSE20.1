# NGBSE20.1

[![CI](https://github.com/E-AI-MODEL/NGBSE20.1/actions/workflows/ci.yml/badge.svg)](https://github.com/E-AI-MODEL/NGBSE20.1/actions/workflows/ci.yml)

## Quickstart (local)
```bash
python -m pip install --upgrade pip
pip install .[dev]
python -m ngbse20.cli validate-config --seeds data/seeds.jsonl --rules data/rules.json
python -m ngbse20.cli collect --seeds data/seeds.jsonl --out out --async --concurrency 20
python -m ngbse20.cli export_stix --findings out/findings.json --out out/stix_bundle.json
```

## Docker

```bash
cp .env.example .env
docker compose up --build
# resultaten: ./out/findings.json en ./out/stix_bundle.json (na export-stap)
```

## CI

* GitHub Actions draait lint (Ruff), typecheck (mypy), tests (pytest+coverage) en pip-audit.
