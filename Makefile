.PHONY: help install test lint type clean build docker-build docker-run health status metrics production-deploy quick-start benchmark security-audit ci production-ready update-deps backup restore help-install help-docker help-production

# Default target
help:
	@echo "🚀 NGBSE 20.1 - Next-Generation Blind Spot Engine"
	@echo ""
	@echo "Available commands:"
	@echo "  install          Install dependencies and package"
	@echo "  test             Run all tests with coverage"
	@echo "  lint             Run code linting (Ruff)"
	@echo "  type             Run type checking (MyPy)"
	@echo "  clean            Clean build artifacts and cache"
	@echo "  build            Build package distribution"
	@echo "  docker-build     Build Docker image"
	@echo "  docker-run       Run NGBSE in Docker"
	@echo "  health           Check system health"
	@echo "  status           Check pipeline status"
	@echo "  metrics          Get performance metrics"
	@echo "  production-deploy Deploy to production environment"
	@echo "  quick-start      Quick start with sample data"
	@echo "  benchmark        Run performance benchmarks"
	@echo "  security-audit   Run security audit"

# Development commands
install:
	@echo "📦 Installing NGBSE 20.1..."
	pip install -e .
	pip install -r requirements.txt

test:
	@echo "🧪 Running tests..."
	python -m pytest tests/ -v --cov=ngbse20 --cov-report=term-missing

lint:
	@echo "🔍 Running linting..."
	ruff check src/ tests/
	ruff format --check src/ tests/

type:
	@echo "🔍 Running type checking..."
	mypy src/ngbse20/

clean:
	@echo "🧹 Cleaning up..."
	rm -rf build/ dist/ *.egg-info/ .pytest_cache/ .coverage
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

build:
	@echo "🏗️ Building package..."
	python -m build

# Docker commands
docker-build:
	@echo "🐳 Building Docker image..."
	docker build -t ngbse20:latest .

docker-run:
	@echo "🚀 Running NGBSE in Docker..."
	docker run -it --rm -v $(PWD)/out:/app/out ngbse20:latest

# Production monitoring commands
health:
	@echo "🏥 Checking system health..."
	ngbse20 health

status:
	@echo "📊 Checking pipeline status..."
	ngbse20 status

metrics:
	@echo "📈 Getting performance metrics..."
	ngbse20 metrics

# Production deployment
production-deploy:
	@echo "🚀 Deploying to production..."
	@echo "1. Building production Docker image..."
	docker build -t ngbse20:production .
	@echo "2. Running health checks..."
	ngbse20 health
	@echo "3. Validating configuration..."
	ngbse20 validate-config --seeds data/seeds.jsonl --rules data/rules.json
	@echo "4. Running production test..."
	ngbse20 collect --seeds data/seeds.jsonl --out out --async --concurrency 5
	@echo "5. Exporting STIX..."
	ngbse20 export-stix --findings out/findings.json --out out/stix_bundle.json
	@echo "✅ Production deployment completed!"

# Quick start for new users
quick-start:
	@echo "🚀 Quick start with NGBSE 20.1..."
	@echo "1. Setting up environment..."
	python3 -m venv .venv
	.venv/bin/activate && pip install -e .
	@echo "2. Running sample collection..."
	.venv/bin/activate && ngbse20 collect --seeds data/seeds.jsonl --out out --async --concurrency 3
	@echo "3. Exporting to STIX..."
	.venv/bin/activate && ngbse20 export-stix --findings out/findings.json --out out/stix_bundle.json
	@echo "4. Checking health..."
	.venv/bin/activate && ngbse20 health
	@echo "✅ Quick start completed! Check out/ directory for results."

# Performance benchmarking
benchmark:
	@echo "⚡ Running performance benchmarks..."
	@echo "Testing collection performance..."
	time ngbse20 collect --seeds data/seeds.jsonl --out out --async --concurrency 10
	@echo "Testing STIX export performance..."
	time ngbse20 export-stix --findings out/findings.json --out out/stix_bundle.json
	@echo "✅ Benchmark completed!"

# Security audit
security-audit:
	@echo "🔒 Running security audit..."
	pip-audit
	@echo "Checking for known vulnerabilities..."
	safety check
	@echo "✅ Security audit completed!"

# CI/CD pipeline
ci:
	@echo "🔄 Running CI pipeline..."
	make lint
	make type
	make test
	make security-audit
	@echo "✅ CI pipeline completed!"

# Production readiness check
production-ready:
	@echo "🔍 Checking production readiness..."
	@echo "1. Running all tests..."
	make test
	@echo "2. Code quality checks..."
	make lint
	make type
	@echo "3. Security audit..."
	make security-audit
	@echo "4. Health check..."
	ngbse20 health
	@echo "5. Performance test..."
	make benchmark
	@echo "✅ NGBSE 20.1 is PRODUCTION READY!"

# Maintenance commands
update-deps:
	@echo "📦 Updating dependencies..."
	pip install --upgrade -r requirements.txt
	pip install --upgrade -e .

backup:
	@echo "💾 Creating backup..."
	tar -czf "ngbse20-backup-$(date +%Y%m%d-%H%M%S).tar.gz" out/ data/ .env

restore:
	@echo "📥 Restoring from backup..."
	@echo "Usage: make restore BACKUP_FILE=filename.tar.gz"
	tar -xzf $(BACKUP_FILE)

# Help for specific commands
help-install:
	@echo "📦 Install help:"
	@echo "  make install          - Install in development mode"
	@echo "  make install-prod     - Install production dependencies"
	@echo "  make update-deps      - Update all dependencies"

help-docker:
	@echo "🐳 Docker help:"
	@echo "  make docker-build     - Build Docker image"
	@echo "  make docker-run       - Run in Docker"
	@echo "  make docker-push      - Push to registry"

help-production:
	@echo "🚀 Production help:"
	@echo "  make production-deploy - Deploy to production"
	@echo "  make production-ready  - Check production readiness"
	@echo "  make health           - System health check"
	@echo "  make status           - Pipeline status"
	@echo "  make metrics          - Performance metrics"
