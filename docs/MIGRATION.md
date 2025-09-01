# Migration Guide: NGBSE 18.0.0-GA → 20.2.0-GA

This guide helps you migrate from NGBSE 18.0.0-GA to the new 20.2.0-GA release.

## Overview of Changes

NGBSE 20.2.0-GA introduces significant architectural improvements while maintaining backward compatibility for most use cases. The main changes include:

- **Modular Architecture**: Complete refactoring for better maintainability
- **Centralized Configuration**: All config files moved to `config/` directory
- **Enhanced Security**: Improved credential handling and security scanning
- **Comprehensive Testing**: Full test suite with CI/CD pipeline
- **BALLM Integration**: Advanced meta-layer generation capabilities

## Step-by-Step Migration

### 1. Update Repository Structure

#### Before (18.0.0-GA)
```
ngbse/
├── rules.json
├── seeds.jsonl
├── demo_ballm.py
├── simple_ballm_demo.py
├── data/
│   ├── rules.json
│   └── seeds.jsonl
└── src/ngbse20/
```

#### After (20.2.0-GA)
```
ngbse/
├── config/
│   ├── ngbse.config.yml
│   ├── rules.json
│   └── seeds.jsonl
├── examples/
│   ├── demo_ballm.py
│   └── simple_ballm_demo.py
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
└── src/ngbse20/
```

### 2. Migrate Configuration Files

#### Create Config Directory
```bash
mkdir config
```

#### Move and Consolidate Configuration
```bash
# Move main config files
mv rules.json config/
mv seeds.jsonl config/

# Remove duplicates
rm -rf data/

# Create main configuration file
cat > config/ngbse.config.yml << EOF
output_dir: "out"
allowlist: ["*"]
collectors:
  enabled: ["http_web", "shodan", "censys", "leakix"]
scoring:
  default_weights:
    coverage: 0.3
    recency: 0.3
    confidence: 0.4
ballm:
  enabled: true
  model: "gpt-4"
EOF
```

### 3. Update Code Usage

#### Old API (18.0.0-GA)
```python
from ngbse20.runtime.orchestrator import run_pipeline

# Load configuration manually
with open('rules.json') as f:
    rules = json.load(f)

with open('seeds.jsonl') as f:
    seeds = [json.loads(line) for line in f]

# Run pipeline
result = run_pipeline(seeds, rules, metrics, config)
```

#### New API (20.2.0-GA)
```python
from ngbse20.runtime.orchestrator import PipelineOrchestrator

# Initialize orchestrator (loads config automatically)
orchestrator = PipelineOrchestrator("config")

# Run pipeline
result = orchestrator.run_pipeline()
```

#### Backward Compatibility
The old API still works for existing code:
```python
from ngbse20.runtime.orchestrator import run_pipeline

# This still works but is deprecated
result = run_pipeline(seeds, rules, metrics, config)
```

### 4. Update Environment Variables

#### Required Environment Variables
Set up your API credentials as environment variables:

```bash
# Shodan
export SHODAN_API_KEY="your_shodan_key"

# Censys
export CENSYS_API_ID="your_censys_id"
export CENSYS_API_SECRET="your_censys_secret"

# LeakIX
export LEAKIX_API_KEY="your_leakix_key"

# URLScan
export URLSCAN_API_KEY="your_urlscan_key"

# GitHub
export GITHUB_TOKEN="your_github_token"

# News API
export NEWS_API_KEY="your_news_key"

# LLM APIs (for BALLM)
export OPENAI_API_KEY="your_openai_key"
export ANTHROPIC_API_KEY="your_anthropic_key"
```

#### Environment File (Optional)
Create a `.env` file for local development:
```bash
# .env
SHODAN_API_KEY=your_shodan_key
CENSYS_API_ID=your_censys_id
CENSYS_API_SECRET=your_censys_secret
# ... other credentials
```

### 5. Update Docker Usage

#### Old Docker Setup
```dockerfile
# Custom Dockerfile required
FROM python:3.11
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
CMD ["python", "-m", "ngbse20.cli"]
```

#### New Docker Usage
```bash
# Use pre-built image
docker run -e SHODAN_API_KEY=your_key ngbse20:latest

# Or build from source
docker build -t ngbse20:latest .
```

### 6. Update CI/CD Pipeline

#### Old Pipeline
```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run tests
        run: python -m pytest
```

#### New Pipeline
The new CI/CD pipeline includes:
- Code formatting and linting
- Security scanning
- Comprehensive testing
- SBOM generation
- Docker image building

No changes needed - the new pipeline is automatically included.

### 7. Update Tests

#### Old Test Structure
```
tests/
├── test_ballm.py
├── test_config_loader.py
└── test_pipeline.py
```

#### New Test Structure
```
tests/
├── unit/
│   ├── test_config_loader.py
│   ├── test_collector_manager.py
│   └── test_pipeline_stages.py
├── integration/
│   └── test_pipeline_integration.py
└── fixtures/
    └── test_data.py
```

#### Running Tests
```bash
# Run all tests
pytest

# Run unit tests only
pytest tests/unit/

# Run integration tests only
pytest tests/integration/

# Run with coverage
pytest --cov=src/ngbse20 --cov-report=html
```

## Configuration Reference

### Main Configuration (`config/ngbse.config.yml`)

```yaml
# Output directory for results
output_dir: "out"

# Domain allowlist (use ["*"] for all domains)
allowlist: ["*"]

# Collector configuration
collectors:
  enabled: ["http_web", "shodan", "censys", "leakix", "urlscan", "github", "news"]

# Scoring weights
scoring:
  default_weights:
    coverage: 0.3    # Breadth of coverage
    recency: 0.3     # Timeliness
    confidence: 0.4  # Reliability

# BALLM configuration
ballm:
  enabled: true
  model: "gpt-4"     # LLM model for meta-layer generation
```

### Rules Configuration (`config/rules.json`)

```json
[
  {
    "rule_id": "high_confidence_warning",
    "name": "High Confidence Finding",
    "description": "Flag high confidence findings",
    "condition": "finding.confidence > 0.9",
    "action": {
      "type": "warning_flag",
      "message": "High confidence finding detected"
    }
  },
  {
    "rule_id": "block_test_domains",
    "name": "Block Test Domains",
    "description": "Block findings from test domains",
    "condition": "seed.value contains 'test'",
    "action": {
      "type": "hard_block",
      "message": "Test domain blocked"
    }
  }
]
```

### Seeds Configuration (`config/seeds.jsonl`)

```jsonl
{"id": "seed1", "type": "domain", "value": "example.com", "metadata": {"source": "manual"}}
{"id": "seed2", "type": "ip", "value": "1.2.3.4", "metadata": {"source": "threat_intel"}}
{"id": "seed3", "type": "url", "value": "https://example.com/path", "metadata": {"source": "scan"}}
```

## Troubleshooting

### Common Issues

#### 1. Configuration Not Found
**Error**: `Config file config/ngbse.config.yml not found`
**Solution**: Ensure the `config/` directory exists and contains the required files.

#### 2. Credential Validation Failed
**Error**: `Collector shodan disabled - missing credentials`
**Solution**: Set the required environment variables for your collectors.

#### 3. Import Errors
**Error**: `ModuleNotFoundError: No module named 'ngbse20'`
**Solution**: Install the package in development mode:
```bash
pip install -e .
```

#### 4. Test Failures
**Error**: Tests failing with credential errors
**Solution**: Mock the collectors in tests or set test environment variables.

### Getting Help

1. **Documentation**: Check `docs/` directory for detailed documentation
2. **Issues**: Report issues on the project repository
3. **Security**: Report security issues via `SECURITY.md`

## Performance Considerations

### Memory Usage
- The new architecture is more memory-efficient
- Large datasets are processed in streaming fashion
- Configurable output directory management

### Execution Time
- Parallel collection where possible
- Configurable collector enablement
- Optional LLM integration with fallback modes

### Resource Requirements
- Minimum: 2GB RAM, 1 CPU core
- Recommended: 4GB RAM, 2 CPU cores
- For large datasets: 8GB+ RAM, 4+ CPU cores

## Security Considerations

### Credential Management
- All credentials now in environment variables
- No credentials in configuration files
- Automatic credential validation

### Input Validation
- Enhanced input validation and sanitization
- STIX output sanitization
- Rule condition validation

### Supply Chain Security
- Automated dependency vulnerability scanning
- SBOM generation for supply chain transparency
- Regular security updates