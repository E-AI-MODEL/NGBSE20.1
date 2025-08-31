# NGBSE 20.1 Makefile
.PHONY: install run test docker build

# Install dependencies in a virtual environment
install:
python -m venv .venv
. .venv/bin/activate && pip install --upgrade pip && pip install -r requirements.lock && pip install -e .

# Run the demo pipeline locally
run:
ngbse20 demo --seeds seeds.jsonl --rules rules.json --allowlist "*"

# Run tests
test:
pip install pytest
pytest

# Build the Docker image
docker:
docker build -t ngbse:20.1 .

# Run the pipeline using Docker Compose
compose-up:
docker compose up --build

# Stop and remove Docker containers
compose-down:
docker compose down
