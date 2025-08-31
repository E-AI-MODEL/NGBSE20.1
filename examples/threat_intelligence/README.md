# Threat Intelligence Examples
## Practical OSINT Collection Scenarios

---

## 🎯 **Overview**

This directory contains practical examples of using NGBSE 20.1 for threat intelligence collection and analysis.

---

## 📁 **Example Scenarios**

### **1. Malware Campaign Tracking**
- **Purpose**: Monitor ongoing malware campaigns
- **Collectors**: LeakIX, URLScan, News
- **Output**: STIX indicators, threat actors, campaign timeline

### **2. Infrastructure Exposure Assessment**
- **Purpose**: Identify exposed infrastructure and vulnerabilities
- **Collectors**: Shodan, Censys
- **Output**: Vulnerability reports, risk assessments

### **3. Data Breach Monitoring**
- **Purpose**: Track data breaches and credential leaks
- **Collectors**: LeakIX, News, GitHub
- **Output**: Breach notifications, impact assessments

### **4. Threat Actor Profiling**
- **Purpose**: Build comprehensive threat actor profiles
- **Collectors**: All collectors
- **Output**: Threat actor STIX objects, behavioral patterns

---

## 🚀 **Quick Examples**

### **Basic Threat Collection**
```bash
# Run threat intelligence collection
python -m ngbse20.cli run \
  --seeds examples/threat_intelligence/seeds/malware_campaign.jsonl \
  --rules examples/threat_intelligence/rules/threat_detection.json \
  --outdir examples/threat_intelligence/output
```

### **Infrastructure Assessment**
```bash
# Assess infrastructure exposure
python -m ngbse20.cli run \
  --seeds examples/threat_intelligence/seeds/infrastructure.jsonl \
  --rules examples/threat_intelligence/rules/infrastructure.json \
  --outdir examples/threat_intelligence/output
```

---

## 📊 **Expected Outputs**

### **STIX Bundle**
- Threat indicators for each finding
- Threat actor objects
- Vulnerability objects
- Relationship objects

### **BALLM Analysis**
- Epistemic insights about threats
- Curiosity questions for investigation
- Confidence assessments

### **Reports**
- Executive summary
- Technical details
- Recommendations

---

## 🔧 **Customization**

### **Modify Seeds**
Edit the seed files to focus on specific threats, actors, or campaigns.

### **Adjust Rules**
Modify rules to trigger different alerts or actions based on your needs.

### **Add Collectors**
Enable additional collectors by adding API keys to your `.env` file.

---

## 📚 **Related Documentation**

- [User Guide](../../docs/USER_GUIDE.md)
- [API Reference](../../docs/API_REFERENCE.md)
- [Quick Start](../../docs/QUICK_START.md)

---

*Use these examples as starting points for your own threat intelligence operations.*