# NGBSE Quick Start Guide
## Get Up and Running in 5 Minutes

---

## 🚀 **Super Quick Start (5 minutes)**

### **1. Clone & Setup**
```bash
git clone https://github.com/E-AI-MODEL/NGBSE20.2.0-GA.git
cd NGBSE20.2.0-GA
```

### **2. Configure API Keys**
```bash
cp .env.example .env
# Edit .env and add at least one API key
```

### **3. Run Pipeline**
```bash
make run
```

### **4. Check Results**
```bash
ls -la out/
cat out/findings.json
```

**That's it!** 🎉

---

## 📋 **What You Need**

### **Required:**
- Python 3.11+ or Docker (Python 3.11-slim base image)
- At least one OSINT API key (see options below)

### **Python Version Requirements:**
- **Minimum**: Python 3.11 (required)
- **Recommended**: Python 3.12 or 3.13
- **Not Supported**: Python 3.9 or 3.10 (legacy versions)
- **Docker**: Uses Python 3.11-slim base image
- **CI/CD**: Tests on Python 3.11, 3.12, 3.13

### **Environment Setup:**
```bash
# Check Python version
python3 --version  # Should show 3.11+

# If using Python 3.9/3.10, upgrade first:
# Ubuntu/Debian: sudo apt install python3.11
# macOS: brew install python@3.11
# Windows: choco install python311
```

### **Recommended API Keys (choose 2-3):**
- **LeakIX** (`LEAKIX_API_KEY`) - Data breaches
- **Shodan** (`SHODAN_API_KEY`) - Infrastructure
- **News** (`NEWS_API_KEY`) - Recent developments
- **GitHub** (`GITHUB_TOKEN`) - Code intelligence

---

## ⚙️ **Step-by-Step Setup**

### **Step 1: Environment Setup**

```bash
# Copy environment template
cp .env.example .env

# Edit with your API keys
nano .env
```

**Minimum .env configuration:**
```bash
# Choose at least one collector
LEAKIX_API_KEY=your_key_here
SHODAN_API_KEY=your_key_here
NEWS_API_KEY=your_key_here

# Optional: LLM for AI insights
OPENAI_API_KEY=your_key_here
```

### **Step 2: Test Configuration**

```bash
# Check which collectors are active
python -m ngbse20.cli collectors

# Validate your config files
python -m ngbse20.cli validate-config --seeds data/seeds.jsonl --rules data/rules.json
```

### **Step 3: First Run**

```bash
# Run complete pipeline
make run

# Or manually:
python -m ngbse20.cli run --seeds data/seeds.jsonl --rules data/rules.json
```

---

## 🔍 **Understanding Your First Run**

### **What Happens:**
1. **Collection** - Gathers data from active collectors
2. **Scoring** - Evaluates quality of findings
3. **Analysis** - Identifies blind spots and gaps
4. **BALLM** - Generates AI-powered insights
5. **Export** - Creates STIX and reports

### **Output Files:**
```
out/
├── findings.json              # Raw intelligence data
├── stix_bundle.json          # STIX 2.1 threat intel
├── ballm_analysis.json       # AI insights
└── history/                  # Historical data
```

---

## 📝 **Customize Your Collection**

### **Edit Seeds (data/seeds.jsonl)**
```json
{"id": "my-threat", "query": "malware", "type": "leakix", "priority": 1}
{"id": "my-infra", "query": "nginx", "type": "shodan", "priority": 2}
{"id": "my-news", "query": "cyber attack", "type": "news", "priority": 3}
```

### **Edit Rules (data/rules.json)**
```json
[
  {
    "id": "threat-alert",
    "name": "Threat Detection",
    "pattern": "malware|ransomware",
    "action": {"type": "warning_flag", "message": "Threat detected"},
    "weight": 2.0
  }
]
```

---

## 🐳 **Docker Alternative**

If you prefer Docker:

```bash
# Build and run with Docker
docker compose up --build

# Or build manually
docker build -t ngbse20:latest .
docker run -v $(pwd)/data:/app/data -v $(pwd)/out:/app/out ngbse20:latest
```

---

## 🔧 **Troubleshooting**

### **Common Issues:**

#### **"No collectors active"**
```bash
# Check API keys
python -m ngbse20.cli collectors

# Verify environment variables
echo $LEAKIX_API_KEY
```

#### **"Pipeline failed"**
```bash
# Check logs
tail -f logs/ngbse20.log

# Validate config
python -m ngbse20.cli validate-config --seeds data/seeds.jsonl --rules data/rules.json
```

#### **"No findings generated"**
```bash
# Test individual collectors
make test-web
make test-leakix

# Check allowlist in seeds
```

---

## 📚 **Next Steps**

### **Learn More:**
- **User Guide**: [docs/USER_GUIDE.md](USER_GUIDE.md)
- **API Reference**: [docs/API_REFERENCE.md](API_REFERENCE.md)
- **Examples**: [examples/](../examples/)

### **Advanced Usage:**
```bash
# Individual pipeline steps
python -m ngbse20.cli collect --seeds data/seeds.jsonl --out out --collector leakix
python -m ngbse20.cli ballm-analyze --findings out/findings.json --out out/ballm.json

# Custom configuration
python -m ngbse20.cli run --seeds data/seeds.jsonl --rules data/rules.json --outdir custom_out
```

---

## 🆘 **Need Help?**

- **GitHub Issues**: [Report problems](https://github.com/E-AI-MODEL/NGBSE20.1/issues)
- **Documentation**: [Complete guides](.)
- **Examples**: [Sample configs](../examples/)

---

## 🎯 **Success Metrics**

You're ready when:
- ✅ `python -m ngbse20.cli collectors` shows active collectors
- ✅ `make run` completes without errors
- ✅ `out/findings.json` contains data
- ✅ `out/stix_bundle.json` is generated

---

*Ready to start collecting intelligence? Run `make run` and explore your findings!* 🚀