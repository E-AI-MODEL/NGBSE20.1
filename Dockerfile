# NGBSE 20.1 - Complete Engine
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app
COPY requirements.lock /app/requirements.lock
RUN pip install --no-cache-dir -r requirements.lock

COPY . /app

# Install package in editable mode to make CLI available
RUN pip install --no-cache-dir -e .

# Default runtime
CMD ["ngbse20", "demo", "--seeds", "seeds.jsonl", "--allowlist", "*"]
