# NGBSE

NGBSE is an engine for epistemic Open-Source Intelligence (OSINT). It's designed not just to find answers, but to expose the "blind spots" in knowledge: assumptions, gaps, and uncertainties. It transforms Large Language Models from "answer machines" into "curiosity partners".

This tool is the practical implementation of the research paper "From Closure to Curiosity: Blindspot-Aware Large Language Models (BALLMs) and the Next-Generation Blind Spot Engine (NGBSE)".

## Key Features

- **Seed-Driven Analysis**: Start analyses with curated probes (seeds) to guide the search process
- **Multi-Source OSINT Collectors**: Comprehensive data collection from diverse intelligence sources
- **Epistemic Scoring**: Evaluate findings based on source credibility, content, and recency
- **Blindspot Analysis**: Identify gaps in collected data regarding coverage, recency, and reliability
- **BALLM Integration**: Blindspot-Aware Large Language Models that interpret blindspots and generate curiosity questions
- **Centralized LLM Management**: Unified configuration and provider abstraction for all LLM operations
- **Deterministic Output**: Reproducible results with fixed seeds and parameter validation
- **JSON Schema Validation**: Structured output validation and normalization
- **STIX 2.1 Export**: Export results in a standardized format for cybersecurity applications
- **Reproducible & Scalable**: Fully containerized with Docker for consistent and easy deployment

## OSINT Collectors

NGBSE 20.2.0-GA includes comprehensive OSINT collectors for threat intelligence:

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

## LLM Management

NGBSE 20.2 introduces centralized LLM management with provider abstraction and deterministic output:

### **Supported Providers**
- **OpenAI**: GPT-4o, GPT-4o-mini, GPT-4, GPT-3.5-turbo
- **Anthropic**: Claude-3.5-Sonnet, Claude-3.5-Haiku, Claude-3-Opus
- **Mistral**: Mistral-Large, Mistral-Medium, Mistral-Small
- **Ollama**: Local models (Llama, Mistral, CodeLlama, Phi3)

### **Configuration**
LLM settings are centrally managed in `config/ngbse.config.yml`:

```yaml
llm:
  provider: openai
  model: gpt-4o-mini
  params:
    temperature: 0.0
    top_p: 1.0
    max_tokens: 400
  seed: 42

profiles:
  deterministic:
    temperature: 0.0
    top_p: 1.0
  extract:
    temperature: 0.0
    top_p: 1.0
    max_tokens: 2000
  creative:
    temperature: 0.7
    top_p: 0.9
    max_tokens: 600
```

### **CLI Commands**
```bash
# List available models for a provider
ngbse llm list-models --provider openai

# Get default model for a provider
ngbse llm default-model --provider anthropic

# Run with LLM overrides
ngbse run --seeds seeds.jsonl --rules rules.json \
  --llm.provider mistral --llm.model mistral-small-latest \
  --llm.temperature 0.3 --profile creative
```

### **Environment Variables**
Override configuration via environment variables:
```bash
export NGBSE_LLM_PROVIDER=anthropic
export NGBSE_LLM_MODEL=claude-3-5-sonnet-20241022
export NGBSE_LLM_TEMPERATURE=0.0
export NGBSE_LLM_MAX_TOKENS=800
export NGBSE_LLM_SEED=42
```

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
