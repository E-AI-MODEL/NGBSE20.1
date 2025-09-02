# NGBSE 20.1 User Guide
## Complete OSINT Intelligence Engine

---

## 📖 **Table of Contents**

1. [Introduction](#introduction)
2. [Quick Start](#quick-start)
3. [Configuration](#configuration)
4. [OSINT Collectors](#osint-collectors)
5. [Pipeline Operations](#pipeline-operations)
6. [Output & Reports](#output--reports)
7. [Advanced Usage](#advanced-usage)
8. [Troubleshooting](#troubleshooting)
9. [Examples](#examples)

---

## 🎯 **Introduction**

### **What is NGBSE 20.1?**

NGBSE 20.1 (Next-Generation Blind Spot Engine) is a comprehensive Open-Source Intelligence (OSINT) engine designed to:

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
git clone https://github.com/E-AI-MODEL/NGBSE20.1.git
cd NGBSE20.1

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
   
   # For AI-powered insights
   OPENAI_API_KEY=your_key_here
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
# Available NGBSE 20.1 Collectors:
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

### **Common Issues**

#### **1. Collector Not Working**
```bash
# Check API key configuration
python -m ngbse20.cli collectors

# Verify environment variables
echo $LEAKIX_API_KEY
echo $SHODAN_API_KEY
```

#### **2. Pipeline Fails**
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
- **E-AI Model**: [Research framework](https://sites.google.com/view/eaimodel)
- **Community**: Join discussions and share use cases

---

## 📄 **License**

This project is licensed under a Commercial License Agreement. This software is proprietary and confidential to the E-AI-MODEL research initiative.

**Commercial Use**: This software is licensed for commercial use under specific terms and conditions outlined in the LICENSE file.

**Restrictions**: Redistribution, modification, reverse engineering, and public distribution are not permitted without explicit written consent.

For licensing inquiries, please contact the E-AI-MODEL research initiative.

---

*Last updated: September 2025*
*Version: 20.1.1*
