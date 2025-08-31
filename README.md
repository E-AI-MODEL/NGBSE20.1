# NGBSE20.1

NGBSE 20.1 is an engine for epistemic Open-Source Intelligence (OSINT). It's designed not just to find answers, but to expose the "blind spots" in knowledge: assumptions, gaps, and uncertainties. It transforms Large Language Models from "answer machines" into "curiosity partners".

This tool is the practical implementation of the research paper "From Closure to Curiosity: Blindspot-Aware Large Language Models (BALLMs) and the Next-Generation Blind Spot Engine (NGBSE)".

## Key Features

- **Seed-Driven Analysis**: Start analyses with curated probes (seeds) to guide the search process
- **Asynchronous Collectors**: Efficiently collect data from web sources with respect for robots.txt and per-domain rate limiting
- **Epistemic Scoring**: Evaluate findings based on source credibility, content, and recency
- **Blindspot Analysis**: Identify gaps in collected data regarding coverage, recency, and reliability
- **BALLM Integration**: Blindspot-Aware Large Language Models that interpret blindspots and generate curiosity questions
- **STIX 2.1 Export**: Export results in a standardized format for cybersecurity applications
- **Reproducible & Scalable**: Fully containerized with Docker for consistent and easy deployment

## Architecture

The NGBSE pipeline follows a modular approach:
```
Seeds → Collect → Enrich & Score → Dual Output (Answers + Blindspots) → BALLM Meta-Layer → STIX Export
```

The BALLM (Blindspot-Aware Large Language Models) layer transforms raw blindspot data into:
- **Epistemic Insights**: LLM-powered interpretation of knowledge gaps
- **Curiosity Questions**: Automatically generated questions to explore blind spots
- **Epistemic Humility**: Quantified awareness of knowledge limitations
- **Productive Failures**: Identification of learning opportunities from gaps

## Quickstart

There are two ways to use NGBSE20.1: locally via Python or via Docker (recommended).

### Docker (Recommended)

The easiest way to get started is with Docker Compose. This ensures the environment is always correct.

1. **Clone the repository:**
   ```bash
   git clone https://github.com/E-AI-MODEL/NGBSE20.1.git
   cd NGBSE20.1
   ```

2. **Configure your environment:**
   Copy the example file and fill in any API keys you want to use for LLM integrations.
   ```bash
   cp .env.example .env
   ```

3. **Start the pipeline:**
   This command builds the Docker image and runs the complete pipeline.
   ```bash
   docker compose up --build
   ```

4. **View results:**
   Results are stored in the `out/` directory.
   - `out/findings.json`: Raw findings
   - `out/stix_bundle.json`: Findings exported to STIX 2.1
   - `out/history/`: Historical asset scores for trend analysis

### Local (Python)

For local installation, Python 3.11+ is required.

1. **Clone the repository:**
   ```bash
   git clone https://github.com/E-AI-MODEL/NGBSE20.1.git
   cd NGBSE20.1
   ```

2. **Install dependencies:**
   It's recommended to do this in a virtual environment.
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install .[dev]
   ```

3. **Run the complete pipeline:**
   The new unified command runs everything from collection to export in one go.
   ```bash
   # Run the complete pipeline (recommended)
   make run
   
   # Or directly:
   python -m ngbse20.cli run --seeds data/seeds.jsonl --rules data/rules.json --outdir out
   ```

4. **Individual pipeline steps (legacy):**
   You can still run individual steps if needed.
   
   **Validate configuration:**
   ```bash
   python -m ngbse20.cli validate-config --seeds data/seeds.jsonl --rules data/rules.json
   ```
   
   **Collect data:**
   ```bash
   python -m ngbse20.cli collect --seeds data/seeds.jsonl --out out --async --concurrency 20
   ```
   
   **Export to STIX:**
   ```bash
   python -m ngbse20.cli export-stix --findings out/findings.json --out out/stix_bundle.json
   ```

## Command-Line Interface (CLI)

The tool is controlled via `ngbse20.cli`:

- **`run`**: Run the complete NGBSE pipeline from collection to reporting (recommended)
  ```bash
  ngbse20 run --seeds <path> --rules <path> [--outdir <dir>] [--allowlist <domains>]
  ```

- **`validate-config`**: Validates the syntax of seeds and rules files
  ```bash
  ngbse20 validate-config --seeds <path> --rules <path>
  ```

- **`collect`**: Starts the data collection pipeline
  ```bash
  ngbse20 collect --seeds <path> --out <dir> [--async] [--concurrency <int>]
  ```

- **`export-stix`**: Converts JSON findings to a STIX 2.1 bundle
  ```bash
  ngbse20 export-stix --findings <path> --out <path>
  ```

- **`ballm-analyze`**: Run BALLM analysis to generate epistemic insights and curiosity questions
  ```bash
  ngbse20 ballm-analyze --findings <path> --out <path> [--depth <int>]
  ```

## Configuration

- **data/seeds.jsonl**: This file contains the starting points (URLs) for the collector. Each line is a JSON object.
- **data/rules.json**: Defines rules that can be applied during analysis (functionality in development).
- **.env**: Store your API keys and other secrets here. Use `.env.example` as a template.

## Development

- **Linting:** `make lint` (uses Ruff)
- **Type Checking:** `make type` (uses MyPy)
- **Testing:** `make test` (uses Pytest)
- **Complete Pipeline:** `make run` (runs the full NGBSE pipeline)

## Research Context

This project implements the research described in "From Closure to Curiosity: Blindspot-Aware Large Language Models (BALLMs) and the Next-Generation Blind Spot Engine (NGBSE)" by Hans Visser (August 2025). The work addresses the epistemic shallowness of current LLMs and proposes a framework for making AI systems more aware of their knowledge gaps and limitations.

## License

This project is part of the E-AI-MODEL research initiative.
