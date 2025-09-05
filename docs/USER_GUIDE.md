# NGBSE User Guide
## Complete OSINT Intelligence Engine

---

## 📖 **Table of Contents**

1. [Introduction](#introduction)
2. [Quick Start](#quick-start)
3. [Configuration](#configuration)
4. [OSINT Collectors](#osint-collectors)
5. [Pipeline Operations](#pipeline-operations)
6. [Output & Reports](#output--reports)
7. [Modular Export System](#modular-export-system)
8. [Enhanced Collector Management](#enhanced-collector-management)
9. [Advanced Usage](#advanced-usage)
10. [Troubleshooting](#troubleshooting)
11. [Examples](#examples)

---

## 🎯 **Introduction**

### **What is NGBSE 20.3?**

NGBSE 20.3 (Next-Generation Blind Spot Engine) is a comprehensive Open-Source Intelligence (OSINT) engine designed to:

- **Collect intelligence** from multiple sources (web, threat feeds, infrastructure, code repositories)
- **Identify blind spots** in your intelligence gathering
- **Generate insights** using AI-powered analysis (BALLM)
- **Export results** in professional formats (STIX 2.1, DOCX reports)

### **Key Concepts**

- **Seeds**: Starting points for intelligence collection
- **Collectors**: Specialized modules for different data sources
- **Pipeline**: Automated workflow from collection to reporting
- **BALLM**: Blindspot-Aware Large Language Model for AI-powered insights

---

## 🚀 **Quick Start**

### **1. Installation**

```bash
# Clone the repository
git clone https://github.com/E-AI-MODEL/NGBSE20.3.git
cd NGBSE20.3

# Install dependencies
make install

# Or with Docker (recommended)
docker compose up --build
```

### **2. First Run**

```bash
# Run the complete pipeline
make run

# Or directly
python -m ngbse20.cli run --seeds data/seeds.jsonl --rules data/rules.json
```

### **3. Check Results**

```bash
# View output directory
ls -la out/

# Check findings
cat out/findings.json

# View STIX export
cat out/stix_bundle.json
```

---

## ⚙️ **Configuration**

### **Environment Setup**

1. **Copy environment template:**
   ```bash
   cp .env.example .env
   ```

2. **Configure API keys** (at least one required):
   ```bash
   # For threat intelligence
   LEAKIX_API_KEY=your_key_here
   SHODAN_API_KEY=your_key_here
   CENSYS_API_ID=your_id_here
   CENSYS_API_SECRET=your_secret_here
   URLSCAN_API_KEY=your_key_here
   
   # For code intelligence
   GITHUB_TOKEN=your_token_here
   
   # For news intelligence
   NEWS_API_KEY=your_key_here
   
   # For AI-powered insights (LLM Configuration)
   OPENAI_API_KEY=your_key_here
   ANTHROPIC_API_KEY=your_key_here
   COHERE_API_KEY=your_key_here
   GOOGLE_API_KEY=your_key_here
   ```

### **Seed Configuration**

**Seeds** define what to collect. Each seed specifies:
- `id`: Unique identifier
- `query`: Search term or URL
- `type`: Collector type
- `priority`: Collection priority (1-10)
- `tags`: Categorization labels

**Example seeds.jsonl:**
```json
{"id": "threat-1", "query": "malware", "type": "leakix", "priority": 1, "tags": ["threat"]}
{"id": "infra-1", "query": "nginx", "type": "shodan", "priority": 2, "tags": ["infrastructure"]}
{"id": "code-1", "query": "ransomware", "type": "github", "priority": 3, "tags": ["code"]}
{"id": "news-1", "query": "cyber attack", "type": "news", "priority": 4, "tags": ["news"]}
```

### **Rule Configuration**

**Rules** define how to process findings:
- `id`: Unique identifier
- `name`: Human-readable name
- `pattern`: Regex pattern to match
- `action`: What to do when matched
- `weight`: Importance score (0-10)

**Example rules.json:**
```json
[
  {
    "id": "threat-detection",
    "name": "Threat Detection",
    "pattern": "malware|ransomware|phishing",
    "action": {"type": "warning_flag", "message": "Threat indicator detected"},
    "weight": 2.0,
    "enabled": true
  }
]
```

---

## 🤖 **LLM Configuration**

### **Dynamic LLM Provider Selection**

NGBSE 20.3 features intelligent LLM provider selection based on available API keys. The system automatically detects which providers are configured and selects the most appropriate model.

### **Supported LLM Providers**

| Provider | Models | API Key | Configuration |
|----------|--------|---------|---------------|
| **OpenAI** | GPT-4, GPT-3.5-turbo, GPT-4o-mini | `OPENAI_API_KEY` | Direct API key |
| **Azure OpenAI** | GPT-4, GPT-3.5-turbo variants | `AZURE_OPENAI_API_KEY` | Key + Endpoint + Version |
| **Anthropic** | Claude-3.5-Sonnet, Claude-3-Haiku | `ANTHROPIC_API_KEY` | Direct API key |
| **Cohere** | Command, Command-Light | `COHERE_API_KEY` | Direct API key |
| **Google** | Gemini-Pro, Gemini-Pro-Vision | `GOOGLE_API_KEY` | Direct API key |

### **Model Selection Logic**

1. **Priority Order**: OpenAI → Azure OpenAI → Anthropic → Cohere → Google
2. **Model Mapping**: Generic model preferences are mapped to provider-specific models
3. **Fallback**: If preferred model unavailable, uses best available alternative

**Example Model Mappings:**
```yaml
# If you specify "gpt-4" but only have Anthropic API key:
gpt-4 → claude-3.5-sonnet

# If you specify "claude-3.5-sonnet" but only have OpenAI API key:
claude-3.5-sonnet → gpt-4o-mini
```

### **LLM Configuration in ngbse.config.yml**

```yaml
ballm:
  enabled: true
  model: "gpt-4"  # Preferred model (auto-mapped to available provider)
  
  # Optional: Provider-specific overrides
  provider_models:
    openai: "gpt-4o-mini"
    anthropic: "claude-3.5-sonnet"
    cohere: "command"
    google: "gemini-pro"
```

### **Environment Variables for LLM Models**

```bash
# Model preferences (optional)
OPENAI_MODEL=gpt-4o-mini
ANTHROPIC_MODEL=claude-3.5-sonnet
COHERE_MODEL=command
GOOGLE_MODEL=gemini-pro
```

---

## 🔍 **OSINT Collectors**

### **Available Collectors**

| Collector | Type | Purpose | API Key Required |
|-----------|------|---------|------------------|
| **HttpWeb** | `web` | Web scraping | No |
| **LeakIX** | `leakix` | Data breaches | `LEAKIX_API_KEY` |
| **Shodan** | `shodan` | IoT/Infrastructure | `SHODAN_API_KEY` |
| **Censys** | `censys` | Network intelligence | `CENSYS_API_ID` + `CENSYS_API_SECRET` |
| **URLScan** | `urlscan` | Threat intelligence | `URLSCAN_API_KEY` |
| **GitHub** | `github` | Code repositories | `GITHUB_TOKEN` |
| **News** | `news` | Recent developments | `NEWS_API_KEY` |

### **Collector Status Check**

```bash
# Check which collectors are active
python -m ngbse20.cli collectors

# Output example:
# Available NGBSE 20.3 Collectors:
# ==================================================
# HttpWebCollector ✅ Active
# LeakIX           ❌ Inactive (missing API keys)
# Shodan           ✅ Active
# Censys           ❌ Inactive (missing API keys)
# URLScan          ❌ Inactive (missing API keys)
# GitHub           ❌ Inactive (missing API keys)
# News             ❌ Inactive (missing API keys)
```

### **Individual Collector Testing**

```bash
# Test specific collectors
make test-leakix
make test-shodan
make test-censys
make test-urlscan
make test-github
make test-news
```

### **HttpWebCollector Allowlist Behavior**

The `HttpWebCollector` handles domain allowlists with the following behavior:

#### **Allowlist Configuration**

```yaml
# Allow all domains (recommended default)
allowlist: ["*"]

# Allow specific domains only
allowlist: ["example.com", "test.org", "*.trusted-domain.com"]

# Empty allowlist - allows all domains (restored behavior)
allowlist: []
```

#### **Behavior Details**

- **`["*"]`**: Allows all domains (wildcard)
- **`["example.com"]`**: Allows only `example.com` and its subdomains
- **`[".example.com"]`**: Allows all subdomains of `example.com`
- **`[]`**: Allows all domains (empty = permissive)

#### **Important Notes**

- **Default Configuration**: Uses `allowlist: ["*"]` for maximum compatibility
- **Empty Allowlist**: In NGBSE 20.3.0, empty allowlist allows all domains (restored behavior)
- **Subdomain Matching**: Use `*.domain.com` or `.domain.com` for subdomain support

---

## 🔄 **Pipeline Operations**

### **Complete Pipeline Run**

```bash
# Run everything from collection to export
python -m ngbse20.cli run \
  --seeds data/seeds.jsonl \
  --rules data/rules.json \
  --outdir out \
  --allowlist "example.com,test.org"
```

**Pipeline Steps:**
1. **Validation** - Check seeds and rules
2. **Collection** - Gather data from all active collectors
3. **Scoring** - Evaluate findings quality
4. **Analysis** - Identify blind spots and gaps
5. **BALLM** - Generate AI-powered insights
6. **Export** - Create STIX and reports

### **Individual Pipeline Steps**

```bash
# Validate configuration
python -m ngbse20.cli validate-config --seeds data/seeds.jsonl --rules data/rules.json

# Collect data only
python -m ngbse20.cli collect --seeds data/seeds.jsonl --out out --collector web

# Export to STIX
python -m ngbse20.cli export-stix --findings out/findings.json --out out/stix_bundle.json

# Run BALLM analysis
python -m ngbse20.cli ballm-analyze --findings out/findings.json --out out/ballm_analysis.json
```

### **Pipeline Configuration**

**Environment Variables:**
```bash
# Pipeline behavior
NGBSE_LOG_LEVEL=INFO                    # Logging detail
NGBSE_BRIEF_MODE=api                    # LLM integration mode
NGBSE_SCENARIO_MODE=api                 # Scenario generation mode

# Collection limits
NGBSE_MAX_FINDINGS=1000                 # Maximum findings per seed
NGBSE_COLLECTION_TIMEOUT=300            # Collection timeout in seconds
```

---

## 📊 **Output & Reports**

### **Output Structure**

```
out/
├── findings.json              # Raw findings from all collectors
├── stix_bundle.json          # STIX 2.1 threat intelligence export
├── ballm_analysis.json       # AI-powered insights and curiosity questions
├── history/                  # Historical asset scores
│   └── YYYYMMDDHHMMSS.asset_scores.json
└── NGBSE_Report_YYYYMMDDHHMMSS.docx  # Professional report
```

### **Findings Format**

Each finding contains:
```json
{
  "id": "unique-identifier",
  "hash": "content-hash",
  "asset": "target-domain-or-ip",
  "raw": {
    "title": "Finding title",
    "description": "Finding description",
    "url": "Source URL"
  },
  "source": {
    "type": "collector-type",
    "url": "Source URL",
    "domain": "Source domain"
  },
  "timestamp": "2025-01-15T10:00:00Z",
  "quality": {"q": 0.8},
  "score": 0.75
}
```

### **STIX 2.1 Export**

- **Indicators**: Threat indicators for each finding
- **Threat Actors**: Identified threat actors
- **Vulnerabilities**: Infrastructure vulnerabilities
- **Notes**: Context and metadata

### **BALLM Analysis**

AI-powered insights including:
- **Epistemic Humility Score**: Confidence in findings
- **Curiosity Questions**: Questions to explore blind spots
- **Productive Failures**: Learning opportunities
- **Epistemic Insights**: Hidden assumptions and biases

---

## 🎓 **Advanced Usage**

### **Custom Collector Configuration**

```json
{
  "collectors": [
    {
      "name": "custom_leakix",
      "enabled": true,
      "api_key": "your_key",
      "rate_limit": 60,
      "timeout": 30,
      "options": {
        "max_results": 100,
        "include_verified": true
      }
    }
  ]
}
```

### **Advanced Seed Types**

```json
{
  "id": "advanced-1",
  "query": "complex search query",
  "type": "leakix",
  "priority": 10,
  "max_findings": 500,
  "tags": ["critical", "threat"],
  "options": {
    "date_range": "2025-01-01:2025-01-15",
    "severity_filter": "high"
  }
}
```

### **Rule Actions**

Available action types:
- `warning_flag`: Mark finding for review
- `hard_block`: Block pipeline execution
- `score_modifier`: Adjust finding score
- `tag_adder`: Add tags to findings

### **Pipeline Customization**

```bash
# Custom pipeline with specific collectors
python -m ngbse20.cli run \
  --seeds data/seeds.jsonl \
  --rules data/rules.json \
  --outdir out \
  --collectors "web,leakix,shodan" \
  --max-findings 2000 \
  --timeout 600
```

---

## 🔧 **Troubleshooting**

### **Python Version Issues**

#### **1. Python Version Too Old**
```bash
# Error: Python 3.9/3.10 not supported
# Solution: Upgrade to Python 3.11+

# Check current version
python3 --version

# Upgrade Python (Ubuntu/Debian)
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-pip

# Upgrade Python (macOS)
brew install python@3.11

# Upgrade Python (Windows)
choco install python311
```

#### **2. Virtual Environment Issues**
```bash
# Error: Virtual environment using old Python version
# Solution: Recreate virtual environment

# Remove old virtual environment
rm -rf venv

# Create new virtual environment with Python 3.11+
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Reinstall dependencies
pip install --upgrade pip
pip install -e .
```

#### **3. Docker Python Version Issues**
```bash
# Error: Docker using Python 3.9
# Solution: Update Dockerfile

# Old Dockerfile
FROM python:3.9-slim AS base

# New Dockerfile
FROM python:3.11-slim AS base
```

### **Common Issues**

#### **4. Collector Not Working**
```bash
# Check API key configuration
python -m ngbse20.cli collectors

# Verify environment variables
echo $LEAKIX_API_KEY
echo $SHODAN_API_KEY
```

#### **5. Pipeline Fails**
```bash
# Check logs
tail -f logs/ngbse20.log

# Validate configuration
python -m ngbse20.cli validate-config --seeds data/seeds.jsonl --rules data/rules.json
```

#### **3. No Findings Generated**
```bash
# Check allowlist configuration
# Verify seed queries
# Test individual collectors
make test-web
make test-leakix
```

#### **4. Memory Issues**
```bash
# Reduce concurrent collectors
export NGBSE_MAX_CONCURRENT_COLLECTORS=3

# Limit findings per seed
# Use smaller allowlists
```

### **Debug Mode**

```bash
# Enable debug logging
export NGBSE_LOG_LEVEL=DEBUG

# Run with verbose output
python -m ngbse20.cli run --seeds data/seeds.jsonl --rules data/rules.json --verbose
```

### **Performance Tuning**

```bash
# Optimize for speed
export NGBSE_MAX_CONCURRENT_COLLECTORS=10
export NGBSE_COLLECTION_TIMEOUT=60

# Optimize for thoroughness
export NGBSE_MAX_FINDINGS=5000
export NGBSE_COLLECTION_TIMEOUT=600
```

---

## 📝 **Examples**

### **Example 1: Threat Intelligence Collection**

**Seeds:**
```json
{"id": "malware-1", "query": "malware", "type": "leakix", "priority": 1}
{"id": "phishing-1", "query": "phishing", "type": "urlscan", "priority": 2}
{"id": "ransomware-1", "query": "ransomware", "type": "github", "priority": 3}
```

**Rules:**
```json
[
  {
    "id": "threat-alert",
    "name": "Threat Alert",
    "pattern": "malware|phishing|ransomware",
    "action": {"type": "warning_flag", "message": "Threat detected"},
    "weight": 3.0
  }
]
```

**Run:**
```bash
python -m ngbse20.cli run --seeds data/seeds.jsonl --rules data/rules.json
```

### **Example 2: Infrastructure Monitoring**

**Seeds:**
```json
{"id": "web-servers", "query": "nginx apache", "type": "shodan", "priority": 1}
{"id": "databases", "query": "mysql postgresql", "type": "shodan", "priority": 2}
{"id": "ssl-certs", "query": "ssl certificate", "type": "censys", "priority": 3}
```

**Rules:**
```json
[
  {
    "id": "infra-alert",
    "name": "Infrastructure Alert",
    "pattern": "nginx|apache|mysql|postgresql",
    "action": {"type": "warning_flag", "message": "Infrastructure component detected"},
    "weight": 2.0
  }
]
```

### **Example 3: News Monitoring**

**Seeds:**
```json
{"id": "cyber-news", "query": "cyber attack", "type": "news", "priority": 1}
{"id": "breach-news", "query": "data breach", "type": "news", "priority": 2}
{"id": "vulnerability-news", "query": "vulnerability disclosure", "type": "news", "priority": 3}
```

---

## 📞 **Support & Resources**

### **Getting Help**

- **GitHub Issues**: [Report bugs and request features](https://github.com/E-AI-MODEL/NGBSE20.1/issues)
- **Documentation**: [Complete API reference](https://github.com/E-AI-MODEL/NGBSE20.1/docs)
- **Examples**: [Sample configurations and use cases](https://github.com/E-AI-MODEL/NGBSE20.1/examples)

### **Additional Resources**

- **Research Paper**: "From Closure to Curiosity: Blindspot-Aware Large Language Models (BALLMs)"
- **E-AI Model**: [Research framework](https://github.com/E-AI-MODEL)
- **Community**: Join discussions and share use cases

---

## 🔄 **Modular Export System**

NGBSE 20.3 includes a comprehensive modular export system supporting multiple output formats for different use cases.

### **Available Export Formats**

#### **CSV Export**
- **Purpose**: Data analysis and spreadsheet import
- **Features**: Customizable delimiters, encoding, and quote characters
- **Use Cases**: Data analysis, Excel import, database integration

```bash
# Export findings to CSV
ngbse20 export --findings findings.json --output data.csv --format csv --target example.com
```

#### **HTML Export**
- **Purpose**: Interactive web reports
- **Features**: Responsive design, search functionality, severity color coding
- **Use Cases**: Web dashboards, client presentations, internal reports

```bash
# Export findings to HTML
ngbse20 export --findings findings.json --output report.html --format html --target example.com
```

#### **DOCX Export**
- **Purpose**: Professional Word documents
- **Features**: Structured reports, metadata sections, recommendations
- **Use Cases**: Business reports, client deliverables, documentation

```bash
# Export findings to DOCX
ngbse20 export --findings findings.json --output report.docx --format docx --target example.com
```

#### **STIX Export**
- **Purpose**: Threat intelligence sharing
- **Features**: STIX 2.1 compliance, indicators, observables, relationships
- **Use Cases**: Threat intelligence platforms, security tools integration

```bash
# Export findings to STIX
ngbse20 export --findings findings.json --output threat_intel.json --format stix --target example.com
```

### **Export Configuration**

#### **Basic Configuration**
```yaml
export:
  formats: ["csv", "html", "docx", "stix"]
  output_dir: "output"
```

#### **Advanced Configuration**
```yaml
export:
  formats: ["csv", "html", "docx", "stix"]
  output_dir: "reports"
  
  # CSV Configuration
  csv_delimiter: ","
  csv_quote_char: '"'
  csv_encoding: "utf-8"
  
  # HTML Configuration
  html_theme: "default"  # default, dark, light, corporate
  html_title: "Security Analysis Report"
  html_template_path: "/path/to/custom_template.html"
  
  # DOCX Configuration
  docx_template_path: "/path/to/custom_template.docx"
  include_charts: true
  include_tables: true
  
  # STIX Configuration
  stix_version: "2.1"  # 2.0 or 2.1
  include_indicators: true
  include_observables: true
  include_relationships: true
```

### **Pipeline Integration**

#### **Multiple Format Export**
```bash
# Run pipeline with multiple export formats
ngbse20 run --seeds seeds.jsonl --rules rules.json --export-formats csv,html,docx,stix
```

#### **Custom Export Configuration**
```yaml
# config/ngbse.config.yml
export:
  formats: ["html", "docx"]  # Only generate HTML and DOCX
  output_dir: "client_reports"
  html_theme: "corporate"
  html_title: "Client Security Assessment"
```

---

## 🔧 **Enhanced Collector Management**

NGBSE 20.3 features an enhanced collector management system with dynamic loading and external collector support.

### **Collector Types**

#### **Built-in Collectors**
- **HttpWebCollector**: Web scraping and content analysis
- **ShodanCollector**: Internet-connected device discovery
- **CensysCollector**: Internet infrastructure scanning
- **LeakIXCollector**: Data leak and vulnerability discovery
- **URLScanCollector**: Website analysis and screenshots
- **GitHubCollector**: Code repository intelligence
- **NewsCollector**: News and media monitoring

#### **External Collectors**
Support for custom collectors through plugin system:
```yaml
collector_manager:
  external_collectors:
    - name: "custom_threat_intel"
      module_path: "/path/to/threat_intel_collector.py"
      class_name: "ThreatIntelCollector"
    - name: "custom_social_media"
      module_path: "/path/to/social_media_collector.py"
      class_name: "SocialMediaCollector"
```

### **API Key Management**

#### **Required API Keys**
| Collector | API Key Required | Environment Variable |
|-----------|------------------|---------------------|
| HttpWebCollector | No | - |
| ShodanCollector | Yes | `SHODAN_API_KEY` |
| CensysCollector | Yes | `CENSYS_API_ID`, `CENSYS_SECRET` |
| LeakIXCollector | Yes | `LEAKIX_TOKEN` |
| URLScanCollector | Yes | `URLSCAN_API_KEY` |
| GitHubCollector | Yes | `GITHUB_TOKEN` |
| NewsCollector | Yes | `NEWS_API_KEY` |

#### **API Key Configuration**
```bash
# Environment variables
export SHODAN_API_KEY="your_shodan_key"
export CENSYS_API_ID="your_censys_id"
export CENSYS_SECRET="your_censys_secret"
export LEAKIX_TOKEN="your_leakix_token"
export URLSCAN_API_KEY="your_urlscan_key"
export GITHUB_TOKEN="your_github_token"
export NEWS_API_KEY="your_news_key"
```

### **Collector Configuration**

#### **Basic Configuration**
```yaml
collector_manager:
  enabled_collectors: ["http_web", "shodan", "censys"]
  auto_discovery: true
  max_concurrent_collectors: 5
```

#### **Advanced Configuration**
```yaml
collector_manager:
  enabled_collectors: []  # Empty = all available
  external_collectors:
    - name: "custom_collector"
      module_path: "/opt/ngbse/collectors/custom.py"
      class_name: "CustomCollector"
  auto_discovery: true
  plugin_directory: "/opt/ngbse/plugins"
  collector_timeout: 300
  max_concurrent_collectors: 10
```

#### **Individual Collector Settings**
```yaml
collectors:
  - name: "shodan"
    enabled: true
    api_key: null  # Set via environment variable
    rate_limit: 1
    timeout: 30
    max_retries: 3
    options:
      facets: ["country", "org", "os"]
      minify: true
  
  - name: "censys"
    enabled: true
    api_key: null
    rate_limit: 1
    timeout: 30
    max_retries: 3
    options:
      index: "ipv4"
      per_page: 100
```

### **Collector Validation**

The system automatically validates collector credentials before initialization:

```bash
# Example output
INFO: Activated collector: http_web
WARNING: Collector shodan disabled - missing API credentials
WARNING: Collector censys disabled - missing API credentials
INFO: Collectors disabled due to missing credentials: ['shodan', 'censys']
INFO: Active collectors: ['HttpWebCollector']
```

### **Custom Collector Development**

#### **Collector Interface**
```python
from ngbse20.collectors.base import BaseCollector

class CustomCollector(BaseCollector):
    def __init__(self, config, allowlist):
        super().__init__(config, allowlist)
        self.api_key = config.get("api_key")
    
    def collect(self, seed, timestamp):
        # Implementation here
        return findings
```

#### **Registration**
```python
from ngbse20.runtime.collector_manager import CollectorManager

manager = CollectorManager(config, credentials)
manager.register_collector("custom", CustomCollector)
```

---

## 📄 **License**

This project is licensed under a Commercial License Agreement. This software is proprietary and confidential to the E-AI-MODEL research initiative.

**Commercial Use**: This software is licensed for commercial use under specific terms and conditions outlined in the LICENSE file.

**Restrictions**: Redistribution, modification, reverse engineering, and public distribution are not permitted without explicit written consent.

For licensing inquiries, please contact the E-AI-MODEL research initiative.

---

*Last updated: September 2025*
*Version: 20.1.1*
