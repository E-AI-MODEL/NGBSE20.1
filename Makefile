.PHONY: install dev lint type test build run run-collect export-stix docker-run clean format security pre-commit validate ballm-analyze collectors

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

sbom:
	python scripts/generate_sbom.py --output-dir . --formats all --validate

sbom-install:
	python scripts/generate_sbom.py --install-syft

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

# Run the complete NGBSE pipeline (recommended)
run:
	python -m ngbse20.cli run --seeds data/seeds.jsonl --rules data/rules.json --outdir out --allowlist "*"

# Run individual pipeline steps (legacy)
run-collect:
	python -m ngbse20.cli collect --seeds data/seeds.jsonl --out out --collector web

export-stix:
	python -m ngbse20.cli export-stix --findings out/findings.json --out out/stix_bundle.json

# Validate configuration files
validate:
	python -m ngbse20.cli validate-config --seeds data/seeds.jsonl --rules data/rules.json

# Run BALLM analysis
ballm-analyze:
	python -m ngbse20.cli ballm-analyze --findings out/findings.json --out out/ballm_analysis.json

# List available collectors and their status
collectors:
	python -m ngbse20.cli collectors

# Test individual collectors
test-leakix:
	python -m ngbse20.cli collect --seeds data/seeds.jsonl --out out --collector leakix

test-shodan:
	python -m ngbse20.cli collect --seeds data/seeds.jsonl --out out --collector shodan

test-censys:
	python -m ngbse20.cli collect --seeds data/seeds.jsonl --out out --collector censys

test-urlscan:
	python -m ngbse20.cli collect --seeds data/seeds.jsonl --out out --collector urlscan

test-github:
	python -m ngbse20.cli collect --seeds data/seeds.jsonl --out out --collector github

test-news:
	python -m ngbse20.cli collect --seeds data/seeds.jsonl --out out --collector news

# Development workflow
dev-setup: install dev pre-commit
	@echo "Development environment setup complete!"

quality: lint type test security
	@echo "All quality checks passed!"

# Quick test of the system
quick-test: validate
	@echo "Configuration validation passed!"
	@echo "Run 'make run' to execute the full pipeline"
	@echo "Run 'make collectors' to see collector status"
