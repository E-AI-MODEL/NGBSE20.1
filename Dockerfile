# syntax=docker/dockerfile:1.7
FROM python:3.11-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app

# systools
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl ca-certificates && rm -rf /var/lib/apt/lists/*

# app deps layer
COPY pyproject.toml /app/
# als je ook een requirements.txt hebt voor pip-audit stap:
COPY requirements.txt /app/ 2>/dev/null || true
RUN pip install --upgrade pip && pip install .  # runtime deps

# ---- runtime image
FROM python:3.11-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY --from=base /usr/local /usr/local
COPY . /app

# standaard loglevel via env
ENV NGBSE_LOGLEVEL=INFO
ENTRYPOINT ["python","-m","ngbse20.cli"]
