# NGBSE 20.1 API Reference
## Complete Technical Documentation

---

## 📖 **Table of Contents**

1. [CLI Commands](#cli-commands)
2. [Configuration Models](#configuration-models)
3. [Collector API](#collector-api)
4. [Pipeline API](#pipeline-api)
5. [Export API](#export-api)
6. [BALLM API](#ballm-api)
7. [Environment Variables](#environment-variables)
8. [Data Formats](#data-formats)

---

## 🖥️ **CLI Commands**

### **Main CLI Interface**

```bash
python -m ngbse20.cli [OPTIONS] COMMAND [ARGS]...
```

**Global Options:**
- `--log-level`: Set logging level (DEBUG|INFO|WARNING|ERROR)
- `--version`: Show version and exit
- `--help`: Show help message

### **Command: `run`**

Execute the complete NGBSE pipeline.

```bash
python -m ngbse20.cli run [OPTIONS]
```

**Options:**
- `--seeds PATH`: Path to seeds.jsonl file (required)
- `--rules PATH`: Path to rules.json file (required)
- `--outdir PATH`: Output directory for results (default: out)
- `--allowlist TEXT`: Comma-separated list of allowed domains (default: *)
- `--metrics TEXT`: JSON string of runtime metrics (default: {})

**Example:**
```bash
python -m ngbse20.cli run \
  --seeds data/seeds.jsonl \
  --rules data/rules.json \
  --outdir results \
  --allowlist "example.com,test.org"
```

### **Command: `validate-config`**

Validate the syntax and structure of seed and rule files.

```bash
python -m ngbse20.cli validate-config [OPTIONS]
```

**Options:**
- `--seeds PATH`: Path to seeds.jsonl file (required)
- `--rules PATH`: Path to rules.json file (required)

**Example:**
```bash
python -m ngbse20.cli validate-config \
  --seeds data/seeds.jsonl \
  --rules data/rules.json
```

### **Command: `collect`**

Collect data from seeds using specified collector.

```bash
python -m ngbse20.cli collect [OPTIONS]
```

**Options:**
- `--seeds PATH`: Path to seeds.jsonl file (required)
- `--out PATH`: Output directory (required)
- `--collector TEXT`: Collector type to use (default: web)
- `--allowlist TEXT`: Comma-separated list of allowed domains (default: *)

**Supported Collectors:**
- `web`: HttpWebCollector
- `leakix`: LeakIXCollector
- `shodan`: ShodanCollector
- `censys`: CensysCollector
- `urlscan`: URLScanCollector
- `github`: GitHubCollector
- `news`: NewsCollector

**Example:**
```bash
python -m ngbse20.cli collect \
  --seeds data/seeds.jsonl \
  --out out \
  --collector leakix \
  --allowlist "example.com"
```

### **Command: `export-stix`**

Convert JSON findings to STIX 2.1 format.

```bash
python -m ngbse20.cli export-stix [OPTIONS]
```

**Options:**
- `--findings PATH`: Path to findings.json file (required)
- `--out PATH`: Output path for STIX bundle (required)

**Example:**
```bash
python -m ngbse20.cli export-stix \
  --findings out/findings.json \
  --out out/stix_bundle.json
```

### **Command: `ballm-analyze`**

Run BALLM analysis to generate epistemic insights and curiosity questions.

```bash
python -m ngbse20.cli ballm-analyze [OPTIONS]
```

**Options:**
- `--findings PATH`: Path to findings.json file (required)
- `--out PATH`: Output path for BALLM analysis (required)
- `--depth INTEGER`: Depth of curiosity questions (1-5, default: 3)

**Example:**
```bash
python -m ngbse20.cli ballm-analyze \
  --findings out/findings.json \
  --out out/ballm_analysis.json \
  --depth 5
```

### **Command: `collectors`**

List all available collectors and their status.

```bash
python -m ngbse20.cli collectors
```

**Output Example:**
```
Available NGBSE 20.1 Collectors:
==================================================
HttpWebCollector ✅ Active
LeakIX           ❌ Inactive (missing API keys)
Shodan           ✅ Active
Censys           ❌ Inactive (missing API keys)
URLScan          ❌ Inactive (missing API keys)
GitHub           ❌ Inactive (missing API keys)
News             ❌ Inactive (missing API keys)
```

---

## ⚙️ **Configuration Models**

### **Seed Model**

```python
class Seed(BaseModel):
    id: str = Field(..., description="Unique identifier for the seed")
    query: str = Field(..., description="Query string or URL for collection")
    type: str = Field("web", description="Collector type")
    asset_id: Optional[str] = Field(None, description="Optional asset identifier")
    tags: list[str] = Field(default_factory=list, description="Tags for categorization")
    priority: int = Field(1, ge=1, le=10, description="Collection priority (1-10)")
    max_findings: Optional[int] = Field(None, ge=1, description="Maximum findings to collect")
```

**Valid Collector Types:**
- `web`: HttpWebCollector
- `leakix`: LeakIXCollector
- `shodan`: ShodanCollector
- `censys`: CensysCollector
- `urlscan`: URLScanCollector
- `github`: GitHubCollector
- `news`: NewsCollector

**Example Seed:**
```json
{
  "id": "threat-1",
  "query": "malware",
  "type": "leakix",
  "asset_id": "asset-1",
  "tags": ["threat", "malware"],
  "priority": 1,
  "max_findings": 100
}
```

### **Rule Model**

```python
class Rule(BaseModel):
    id: str = Field(..., description="Unique rule identifier")
    name: str = Field(..., description="Human-readable rule name")
    pattern: str = Field(..., description="Pattern or condition to match")
    weight: float = Field(1.0, ge=0, le=10, description="Rule weight (0-10)")
    action: dict = Field(default_factory=dict, description="Action to take when rule matches")
    enabled: bool = Field(True, description="Whether rule is active")
    tags: list[str] = Field(default_factory=list, description="Tags for categorization")
```

**Valid Action Types:**
- `warning_flag`: Mark finding for review
- `hard_block`: Block pipeline execution
- `score_modifier`: Adjust finding score
- `tag_adder`: Add tags to findings

**Example Rule:**
```json
{
  "id": "threat-detection",
  "name": "Threat Detection",
  "pattern": "malware|ransomware|phishing",
  "weight": 2.0,
  "action": {
    "type": "warning_flag",
    "message": "Threat indicator detected"
  },
  "enabled": true,
  "tags": ["threat", "security"]
}
```

### **CollectorConfig Model**

```python
class CollectorConfig(BaseModel):
    name: str = Field(..., description="Collector name")
    enabled: bool = Field(True, description="Whether collector is enabled")
    api_key: Optional[str] = Field(None, description="API key for the collector")
    rate_limit: Optional[int] = Field(None, ge=1, description="Rate limit per minute")
    timeout: int = Field(30, ge=1, description="Request timeout in seconds")
    max_retries: int = Field(3, ge=0, description="Maximum retry attempts")
    options: dict = Field(default_factory=dict, description="Collector-specific options")
```

### **Config Model**

```python
class Config(BaseModel):
    seeds: list[Seed] = Field(default_factory=list, description="List of seeds to process")
    rules: list[Rule] = Field(default_factory=list, description="List of rules to apply")
    collectors: list[CollectorConfig] = Field(default_factory=list, description="Collector configurations")
    options: dict[str, str] = Field(default_factory=dict, description="General options")
    
    # Pipeline options
    max_concurrent_collectors: int = Field(5, ge=1, description="Maximum concurrent collectors")
    output_format: str = Field("json", description="Output format (json, stix, docx)")
    enable_ballm: bool = Field(True, description="Enable BALLM meta-layer generation")
    enable_forecasting: bool = Field(True, description="Enable trend forecasting")
    enable_scenarios: bool = Field(True, description="Enable scenario synthesis")
```

---

## 🔍 **Collector API**

### **Base Collector Interface**

All collectors inherit from `BaseCollector`:

```python
class BaseCollector(ABC):
    def __init__(self, config: Dict[str, Any], allowlist_domains: List[str]):
        self.config = config
        self.allow_domains = [d.lower() for d in allowlist_domains]

    def _is_allowed(self, domain: str) -> bool:
        """Check if domain is in allowlist."""
        
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL using tldextract."""
        
    @abstractmethod
    def collect(self, seed: Dict[str, Any], now_iso: str) -> List[Dict[str, Any]]:
        """Collect data from the source. Must be implemented by subclasses."""
        
    def get_collector_info(self) -> Dict[str, Any]:
        """Get information about this collector."""
        
    def _is_active(self) -> bool:
        """Check if collector is active (has required credentials)."""
```

### **HttpWebCollector**

**Purpose:** Web scraping and content analysis

**No API key required**

**Methods:**
```python
def collect(self, seed: Dict[str, Any], now_iso: str) -> List[Dict[str, Any]]:
    """Collect data from web pages."""
```

**Example Usage:**
```python
from ngbse20.collectors import HttpWebCollector

collector = HttpWebCollector(allowlist_domains=["example.com"])
findings = collector.collect(seed, now_iso)
```

### **LeakIXCollector**

**Purpose:** Data breach intelligence and leaked credentials

**Required:** `LEAKIX_API_KEY`

**Methods:**
```python
def collect(self, seed: Dict[str, Any], now_iso: str) -> List[Dict[str, Any]]:
    """Collect data breach intelligence from LeakIX."""
```

**API Endpoint:** `https://leakix.net/api/search`

**Example Usage:**
```python
from ngbse20.collectors import LeakIXCollector

collector = LeakIXCollector(config={}, allowlist=["example.com"])
findings = collector.collect(seed, now_iso)
```

### **ShodanCollector**

**Purpose:** IoT devices, servers, and infrastructure intelligence

**Required:** `SHODAN_API_KEY`

**Methods:**
```python
def collect(self, seed: Dict[str, Any], now_iso: str) -> List[Dict[str, Any]]:
    """Collect IoT and infrastructure intelligence from Shodan."""
```

**API Endpoint:** `https://api.shodan.io/shodan/host/search`

**Example Usage:**
```python
from ngbse20.collectors import ShodanCollector

collector = ShodanCollector(config={}, allowlist=["example.com"])
findings = collector.collect(seed, now_iso)
```

### **CensysCollector**

**Purpose:** Network topology and SSL certificate intelligence

**Required:** `CENSYS_API_ID` + `CENSYS_API_SECRET`

**Methods:**
```python
def collect(self, seed: Dict[str, Any], now_iso: str) -> List[Dict[str, Any]]:
    """Collect network and SSL intelligence from Censys."""
```

**API Endpoint:** `https://search.censys.io/api/v2/hosts/search`

**Example Usage:**
```python
from ngbse20.collectors import CensysCollector

collector = CensysCollector(config={}, allowlist=["example.com"])
findings = collector.collect(seed, now_iso)
```

### **URLScanCollector**

**Purpose:** Threat intelligence and malicious URL detection

**Required:** `URLSCAN_API_KEY`

**Methods:**
```python
def collect(self, seed: Dict[str, Any], now_iso: str) -> List[Dict[str, Any]]:
    """Collect threat intelligence from URLScan."""
```

**API Endpoint:** `https://urlscan.io/api/v1/search/`

**Example Usage:**
```python
from ngbse20.collectors import URLScanCollector

collector = URLScanCollector(config={}, allowlist=["example.com"])
findings = collector.collect(seed, now_iso)
```

### **GitHubCollector**

**Purpose:** Code repository and tool intelligence

**Required:** `GITHUB_TOKEN`

**Methods:**
```python
def collect(self, seed: Dict[str, Any], now_iso: str) -> List[Dict[str, Any]]:
    """Collect code repository intelligence from GitHub."""
```

**API Endpoints:**
- `https://api.github.com/search/repositories`
- `https://api.github.com/search/code`

**Example Usage:**
```python
from ngbse20.collectors import GitHubCollector

collector = GitHubCollector(config={}, allowlist=["github.com"])
findings = collector.collect(seed, now_iso)
```

### **NewsCollector**

**Purpose:** Recent developments and threat intelligence

**Required:** `NEWS_API_KEY`

**Methods:**
```python
def collect(self, seed: Dict[str, Any], now_iso: str) -> List[Dict[str, Any]]:
    """Collect news and recent developments."""
```

**API Endpoints:**
- NewsAPI.org: `https://newsapi.org/v2/everything`
- GNews: `https://gnews.io/api/v4/search`

**Example Usage:**
```python
from ngbse20.collectors import NewsCollector

collector = NewsCollector(config={}, allowlist=["news.com"])
findings = collector.collect(seed, now_iso)
```

---

## 🔄 **Pipeline API**

### **Main Pipeline Function**

```python
def run_pipeline(
    seeds: list[dict[str, Any]],
    rules: list[dict[str, Any]],
    metrics: dict[str, Any] | None = None,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run the complete NGBSE pipeline."""
```

**Parameters:**
- `seeds`: List of seed dictionaries
- `rules`: List of rule dictionaries
- `metrics`: Optional runtime metrics
- `config`: Optional configuration dictionary

**Returns:**
```python
{
    "status": "ok",
    "cai": 0.75,
    "counts": {
        "findings": 150,
        "forecasts": 5,
        "next_seeds": 10,
        "scenarios": 3
    },
    "output_files": {
        "findings": "out/findings.json",
        "stix_bundle": "out/stix_bundle.json",
        "history": "out/history/20250115120000.asset_scores.json"
    },
    "findings": [...],
    "stix": {...},
    "traces": [...],
    "forecast": [...],
    "next_seeds": [...],
    "blindspots": {...},
    "ballm_meta_layer": {...},
    "scenarios": [...],
    "brief": {...}
}
```

### **Pipeline Steps**

1. **Validation Gate**
   - Check rules for hard blocks
   - Return early if blocked

2. **Collection**
   - Build active collectors
   - Collect data from all sources
   - Apply allowlist filtering

3. **Rules Processing**
   - Evaluate non-blocking rules
   - Apply actions to findings

4. **Scoring**
   - Score findings based on quality metrics
   - Apply rule-based modifications

5. **History & Forecast**
   - Aggregate asset scores
   - Build trend forecasts

6. **Seed Proposal**
   - Generate new seeds based on findings

7. **Blindspot Analysis**
   - Identify coverage gaps
   - Detect recency issues
   - Find confidence problems

8. **BALLM Meta-Layer**
   - Generate AI-powered insights
   - Create curiosity questions
   - Calculate epistemic humility

9. **Scenario Synthesis**
   - Build future scenarios
   - Group findings by themes

10. **Export & Reporting**
    - Generate STIX bundle
    - Create DOCX report
    - Write manifest file

### **Pipeline Configuration**

```python
config = {
    "output_dir": "out",
    "allowlist": ["example.com", "test.org"],
    "max_concurrent_collectors": 5,
    "output_format": "all",
    "enable_ballm": True,
    "enable_forecasting": True,
    "enable_scenarios": True
}
```

---

## 📤 **Export API**

### **STIX Export**

```python
def to_stix_bundle(findings: list[dict[str, Any]]) -> Bundle:
    """Create comprehensive STIX bundle from findings."""
```

**STIX Objects Generated:**
- **Indicators**: Threat indicators for each finding
- **Threat Actors**: Identified threat actors
- **Vulnerabilities**: Infrastructure vulnerabilities
- **Notes**: Context and metadata

**Example Usage:**
```python
from ngbse20.export.stix import to_stix_bundle

bundle = to_stix_bundle(findings)
stix_json = bundle.serialize(pretty=True)
```


- Scenario Analysis
- BALLM Insights
- Analyst Recommendations

### **Manifest Generation**

```python
def write_manifest(
    output_dir: str,
    version: str,
    seeds_file: str,
    rules_file: str,
    findings_file: str
) -> str:
    """Generate chain-of-custody manifest."""
```

**Manifest Contents:**
- Pipeline execution details
- Input file hashes
- Output file hashes
- Timestamp information
- Version information

---

## 🧠 **BALLM API**

### **BALLM Meta-Layer Generator**

```python
class BALLMMetaLayerGenerator:
    def __init__(self, llm_client):
        self.blindspot_interpreter = BlindspotInterpretationEngine(llm_client)
        self.curiosity_generator = CuriosityGenerationEngine(llm_client)
    
    def generate_meta_layer(
        self,
        findings: List[Dict[str, Any]],
        blindspots: Dict[str, Any],
        asset_scores: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate the complete BALLM meta-layer output."""
```

**Output Structure:**
```python
{
    "blindspot_interpretation": {...},
    "epistemic_assumptions": [...],
    "curiosity_questions": [...],
    "epistemic_confidence": 0.75,
    "productive_failure_insights": [...],
    "epistemic_humility_score": 0.8,
    "meta_layer_version": "1.0",
    "generation_timestamp": "2025-01-15T12:00:00Z"
}
```

### **Blindspot Interpretation Engine**

```python
class BlindspotInterpretationEngine:
    def interpret_blindspots_with_llm(
        self,
        blindspots: Dict[str, Any],
        findings: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Use LLM to interpret what blindspots mean epistemically."""
    
    def extract_epistemic_insights(
        self,
        blindspots: Dict[str, Any],
        findings: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Extract epistemic insights from blindspots and findings."""
```

### **Curiosity Generation Engine**

```python
class CuriosityGenerationEngine:
    def generate_curiosity_questions(
        self,
        findings: List[Dict[str, Any]],
        blindspots: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate curiosity-driven questions based on blindspots and findings."""
```

**Question Types:**
- `coverage_gap`: Source diversity questions
- `recency_gap`: Temporal analysis questions
- `confidence_gap`: Quality assessment questions
- `llm_generated`: AI-generated insights
- `productive_failure`: Learning opportunity questions

---

## 🌍 **Environment Variables**

### **Core Configuration**

```bash
# Logging
NGBSE_LOG_LEVEL=INFO                    # DEBUG|INFO|WARNING|ERROR

# Pipeline behavior
NGBSE_BRIEF_MODE=api                    # api|prompt
NGBSE_SCENARIO_MODE=api                 # api|prompt
NGBSE_MAX_FINDINGS=1000                 # Maximum findings per seed
NGBSE_COLLECTION_TIMEOUT=300            # Collection timeout in seconds
NGBSE_MAX_CONCURRENT_COLLECTORS=5       # Maximum concurrent collectors
```

### **LLM API Keys**

```bash
# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini

# Azure OpenAI
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_ENDPOINT=https://...
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini

# Anthropic
ANTHROPIC_API_KEY=...
ANTHROPIC_MODEL=claude-3-5-sonnet-20240620

# Google
GOOGLE_API_KEY=...
GOOGLE_MODEL=gemini-1.5-pro
```

### **OSINT Collector API Keys**

```bash
# LeakIX
LEAKIX_API_KEY=...

# Shodan
SHODAN_API_KEY=...

# Censys
CENSYS_API_ID=...
CENSYS_API_SECRET=...

# URLScan
URLSCAN_API_KEY=...

# GitHub
GITHUB_TOKEN=...

# News APIs
NEWS_API_KEY=...                        # NewsAPI.org
GNEWS_API_KEY=...                       # GNews (backup)
```

---

## 📊 **Data Formats**

### **Finding Format**

```python
{
    "id": "unique-identifier",
    "hash": "content-hash",
    "asset": "target-domain-or-ip",
    "raw": {
        "title": "Finding title",
        "description": "Finding description",
        "url": "Source URL",
        # Collector-specific fields
    },
    "source": {
        "type": "collector-type",
        "url": "Source URL",
        "domain": "Source domain"
    },
    "timestamp": "2025-01-15T10:00:00Z",
    "quality": {"q": 0.8},
    "score": 0.75,
    "score_breakdown": {
        "base": 0.6,
        "extras": 0.15,
        "recency": 0.4
    }
}
```

### **Blindspot Format**

```python
{
    "coverage": {
        "ratios": {"web": 0.6, "news": 0.4},
        "max_category": "web",
        "imbalance": 0.2
    },
    "recency": {
        "spike": False,
        "detail": {"2025-01-15": 10, "2025-01-14": 5}
    },
    "confidence": {
        "risky_assets": ["example.com"],
        "n": 1
    }
}
```

### **Trace Format**

```python
{
    "component": "collect",
    "input": {"n_seeds": 5, "n_collectors": 3},
    "output": {"n_findings": 150},
    "message": "collected findings",
    "timestamp": "2025-01-15T12:00:00Z",
    "duration_ms": 2500
}
```

---

## 📞 **Support & Resources**

### **Getting Help**

- **GitHub Issues**: [Report bugs and request features](https://github.com/E-AI-MODEL/NGBSE20.1/issues)
- **Documentation**: [Complete user guide](https://github.com/E-AI-MODEL/NGBSE20.1/docs/USER_GUIDE.md)
- **Examples**: [Sample configurations and use cases](https://github.com/E-AI-MODEL/NGBSE20.1/examples)

### **Additional Resources**

- **Research Paper**: "From Closure to Curiosity: Blindspot-Aware Large Language Models (BALLMs)"
- **E-AI Model**: [Research framework](https://github.com/E-AI-MODEL)
- **Community**: Join discussions and share use cases

---

## 📄 **License**

This project is licensed under a Commercial License Agreement. This software is proprietary and confidential to the E-AI-MODEL research initiative.

**Commercial Use**: This software is licensed for commercial use under specific terms and conditions outlined in the LICENSE file.

**Restrictions**: Redistribution, modification, reverse engineering, and public distribution are not permitted without explicit written consent.

For licensing inquiries, please contact the E-AI-MODEL research initiative.

---

*Last updated: January 2025*
*Version: 20.1.1*