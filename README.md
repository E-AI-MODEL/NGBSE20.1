# NGBSE

NGBSE is an engine for epistemic Open-Source Intelligence (OSINT). It's designed not just to find answers, but to expose the "blind spots" in knowledge: assumptions, gaps, and uncertainties. It transforms Large Language Models from "answer machines" into "curiosity partners".

This tool is the practical implementation of the research paper "From Closure to Curiosity: Blindspot-Aware Large Language Models (BALLMs) and the Next-Generation Blind Spot Engine (NGBSE)".

## Key Features

- **Seed-Driven Analysis**: Start analyses with curated probes (seeds) to guide the search process
- **Multi-Source OSINT Collectors**: Comprehensive data collection from diverse intelligence sources
- **Epistemic Scoring**: Evaluate findings based on source credibility, content, and recency
- **Blindspot Analysis**: Identify gaps in collected data regarding coverage, recency, and reliability
- **BALLM Integration**: Blindspot-Aware Large Language Models that interpret blindspots and generate curiosity questions
- **STIX 2.1 Export**: Export results in a standardized format for cybersecurity applications
- **Reproducible & Scalable**: Fully containerized with Docker for consistent and easy deployment

## LLM Configuration

NGBSE 20.3.0-GA features dynamic LLM provider selection based on available API keys. The system automatically detects which LLM providers are configured and selects the appropriate model.

### **Supported LLM Providers**
- **OpenAI**: GPT-4, GPT-3.5-turbo, GPT-4o-mini
- **Azure OpenAI**: GPT-4, GPT-3.5-turbo variants
- **Anthropic**: Claude-3.5-Sonnet, Claude-3-Haiku
- **Cohere**: Command, Command-Light
- **Google**: Gemini-Pro, Gemini-Pro-Vision

### **LLM Configuration**
Configure your preferred LLM provider by setting the appropriate API key in `.env`:

```bash
# OpenAI (default if available)
OPENAI_API_KEY=your_openai_key_here

# Azure OpenAI
AZURE_OPENAI_API_KEY=your_azure_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-02-15-preview

# Anthropic
ANTHROPIC_API_KEY=your_anthropic_key_here

# Cohere
COHERE_API_KEY=your_cohere_key_here

# Google
GOOGLE_API_KEY=your_google_key_here
```

### **Model Selection**
The system automatically maps your preferred model to the available provider:
- If you specify `gpt-4` but only have Anthropic API key → uses `claude-3.5-sonnet`
- If you specify `claude-3.5-sonnet` but only have OpenAI API key → uses `gpt-4o-mini`
- Configuration in `ngbse.config.yml` allows fine-tuning of model preferences

## OSINT Collectors

NGBSE 20.3.0-GA includes comprehensive OSINT collectors for threat intelligence:

### **Core Collectors**
- **HttpWebCollector**: Web scraping and content analysis
- **LeakIX**: Data breach intelligence and leaked credentials
- **Shodan**: IoT devices, servers, and infrastructure intelligence
- **Censys**: Network topology and SSL certificate intelligence
- **URLScan**: Threat intelligence and malicious URL detection
- **GitHub**: Code repository and tool intelligence
- **News**: Recent developments and threat intelligence

### **Collector Configuration**
Each collector automatically activates when its API key is configured in `.env`:
```bash
# Example .env configuration
LEAKIX_API_KEY=your_key_here
SHODAN_API_KEY=your_key_here
CENSYS_API_ID=your_id_here
CENSYS_API_SECRET=your_secret_here
URLSCAN_API_KEY=your_key_here
GITHUB_TOKEN=your_token_here
NEWS_API_KEY=your_key_here
```

## Architecture

The NGBSE pipeline follows a modular approach:
```
Seeds → Multi-Collector Data Gathering → Enrich & Score → Dual Output (Answers + Blindspots) → BALLM Meta-Layer → STIX Export
```

The BALLM (Blindspot-Aware Large Language Models) layer transforms raw blindspot data into:
- **Epistemic Insights**: LLM-powered interpretation of knowledge gaps
- **Curiosity Questions**: Automatically generated questions to explore blind spots
- **Epistemic Humility**: Quantified awareness of knowledge limitations
- **Productive Failures**: Identification of learning opportunities from gaps

## Quickstart

There are two ways to use NGBSE20.3: locally via Python or via Docker (recommended).

### Docker (Recommended)

The easiest way to get started is with Docker Compose. This ensures the environment is always correct.

1. **Clone the repository:**
   ```bash
   git clone https://github.com/E-AI-MODEL/NGBSE20.3.git
   cd NGBSE20.3
   ```

2. **Configure your environment:**
   Copy the example file and fill in any API keys you want to use for LLM integrations and OSINT collectors.
   ```bash
   cp .env.example .env
   # Edit .env and add your API keys
   ```

3. **Start the pipeline:**
   This command builds the Docker image and runs the complete pipeline.
   ```bash
   docker compose up --build
   ```

4. **View results:**
   Results are stored in the `out/` directory.
   - `out/findings.json`: Raw findings from all collectors
   - `out/stix_bundle.json`: Findings exported to STIX 2.1
   - `out/history/`: Historical asset scores for trend analysis

### Local (Python)

For local installation, Python 3.11+ is required.

**Python Version Compatibility:**
- **Minimum**: Python 3.11
- **Recommended**: Python 3.12
- **Docker**: Uses Python 3.11-slim base image
- **CI/CD**: Tests on Python 3.11, 3.12

**Version Support Matrix:**
| Python Version | Status | Notes |
|----------------|--------|-------|
| 3.9.x | ❌ **Not Supported** | Legacy version, use 3.11+ |
| 3.10.x | ❌ **Not Supported** | Legacy version, use 3.11+ |
| 3.11.x | ✅ **Fully Supported** | Minimum required version |
| 3.12.x | ✅ **Fully Supported** | Recommended for development |
| 3.13.x | ⚠️ **Not Tested** | Compatibility issues with dependencies |

1. **Clone the repository:**
   ```bash
   git clone https://github.com/E-AI-MODEL/NGBSE20.3.git
   cd NGBSE20.3
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

## New in Scoring v18.1

- **Source Trust Scoring**: Evaluate findings based on domain trustworthiness
- **Keyword Pattern Scoring**: Enhanced relevance scoring with configurable rules  
- **Shadow Mode**: Safe rollout with side-by-side comparison
- **Enhanced Observability**: Detailed metrics and contributor tracking

See [Scoring v18.1 Documentation](docs/SCORING_V18_1.md) for details.

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

### **Seed Types**
Configure different collector types in your seeds:
```json
{"id": "web-1", "query": "https://example.com", "type": "web"}
{"id": "threat-1", "query": "malware", "type": "leakix"}
{"id": "infra-1", "query": "nginx", "type": "shodan"}
{"id": "code-1", "query": "ransomware", "type": "github"}
{"id": "news-1", "query": "cyber attack", "type": "news"}
```

## Development

- **Linting:** `make lint` (uses Ruff)
- **Type Checking:** `make type` (uses MyPy)
- **Testing:** `make test` (uses Pytest)
- **Complete Pipeline:** `make run` (runs the full NGBSE pipeline)

## Research Context

This project implements the research described in "From Closure to Curiosity: Blindspot-Aware Large Language Models (BALLMs) and the Next-Generation Blind Spot Engine (NGBSE)" by Hans Visser (August 2025). The work addresses the epistemic shallowness of current LLMs and proposes a framework for making AI systems more aware of their knowledge gaps and limitations.

## License

This project is licensed under a Commercial License Agreement. This software is proprietary and confidential to the E-AI-MODEL research initiative.

**Commercial Use**: This software is licensed for commercial use under specific terms and conditions outlined in the LICENSE file.

**Restrictions**: Redistribution, modification, reverse engineering, and public distribution are not permitted without explicit written consent.

For licensing inquiries, please contact the E-AI-MODEL research initiative.
