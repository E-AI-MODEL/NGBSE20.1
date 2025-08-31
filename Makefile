.PHONY: install dev lint type test build run export-stix docker-run

install:
	python -m pip install --upgrade pip
	pip install .

dev:
	pip install .[dev]

lint:
	ruff check .

type:
	mypy --strict ngbse20

test:
		pytest -q --cov=ngbse20

build:
		docker build -t ngbse20:latest .

run:
		python -m ngbse20.cli collect --seeds data/seeds.jsonl --out out --async --concurrency 20

export-stix:
			python -m ngbse20.cli export_stix --findings out/findings.json --out out/stix_bundle.json

docker-run:
			docker compose up --build
