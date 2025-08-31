.PHONY: install dev lint type test build run export-stix docker-run clean format security pre-commit

install:
	python -m pip install --upgrade pip
	pip install .

dev:
	pip install .[dev]

lint:
	ruff check .

format:
	ruff format .
	black .

type:
	mypy --strict src/ngbse20

test:
	pytest -q --cov=ngbse20 --cov-report=html

test-watch:
	pytest -q --cov=ngbse20 --cov-report=html -f

security:
	bandit -r src/ngbse20
	pip-audit -r requirements.txt || true

pre-commit:
	pre-commit install
	pre-commit run --all-files

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete
	find . -name "*.pyo" -delete
	find . -name "*.pyd" -delete
	rm -rf build/ dist/ *.egg-info/ .coverage coverage.xml .pytest_cache/ .mypy_cache/ .ruff_cache/

build:
	docker build -t ngbse20:latest .

run:
	python -m ngbse20.cli collect --seeds data/seeds.jsonl --out out --async --concurrency 20

export-stix:
	python -m ngbse20.cli export_stix --findings out/findings.json --out out/stix_bundle.json

docker-run:
	docker compose up --build

# Development workflow
dev-setup: install dev pre-commit
	@echo "Development environment setup complete!"

quality: lint type test security
	@echo "All quality checks passed!"
