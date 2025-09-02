# NGBSE 20.1 Makefile

.PHONY: format check install test clean

# Format code with isort and black
format:
	isort src/ tests/
	black src/ tests/

# Check formatting without making changes
check:
	isort --check-only src/ tests/
	black --check src/ tests/

# Install dependencies
install:
	pip install -r requirements-dev.txt

# Run tests
test:
	pytest tests/

# Clean up
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf .pytest_cache/
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/

# Development setup
dev-setup: install
	pre-commit install

# Quick format and commit
quick-format: format
	git add .
	git commit -m "fix: apply isort and black formatting"
