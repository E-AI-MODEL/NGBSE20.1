# NGBSE 20.2 Architecture

## Overview

NGBSE (Next-Generation Business Security Engine) 20.2 is a modular threat intelligence pipeline that collects, scores, and analyzes security findings from multiple sources. The system is designed with a clear separation of concerns and follows a staged pipeline architecture.

## System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Config Loader │    │ Collector Mgr   │    │ Pipeline Stages │
│                 │    │                 │    │                 │
│ • Load config   │    │ • Build collectors│   │ • Validate      │
│ • Load rules    │    │ • Cred validation│   │ • Collect       │
│ • Load seeds    │    │ • Collection    │   │ • Score         │
│ • Get credentials│   │                 │   │ • Forecast      │
└─────────────────┘    └─────────────────┘    │ • BALLM         │
         │                       │             │ • Export        │
         └───────────────────────┼─────────────┘
                                 │
                    ┌─────────────────┐
                    │   Orchestrator  │
                    │                 │
                    │ • Coordinate    │
                    │ • Error handling│
                    │ • Result format │
                    └─────────────────┘
```

## Core Components

### 1. Configuration Management (`src/ngbse20/config/`)

**ConfigLoader**: Centralized configuration management
- Loads main configuration from `config/ngbse.config.yml`
- Manages rules from `config/rules.json`
- Handles seeds from `config/seeds.jsonl`
- Extracts credentials from environment variables

### 2. Collection Layer (`src/ngbse20/collectors/`)

**CollectorManager**: Manages collector lifecycle
- Registry of available collectors
- Credential validation
- Collector instantiation and filtering

**Available Collectors**:
- `HttpWebCollector`: Web scraping and content analysis
- `ShodanCollector`: Shodan API integration
- `CensysCollector`: Censys API integration
- `LeakIXCollector`: LeakIX API integration
- `URLScanCollector`: URLScan.io integration
- `GitHubCollector`: GitHub repository scanning
- `NewsCollector`: News and threat intelligence feeds

### 3. Pipeline Processing (`src/ngbse20/runtime/`)

**PipelineStages**: Modular pipeline stages
1. **Validation**: Hard block rule evaluation
2. **Collection**: Multi-collector data gathering
3. **Rules**: Non-blocking rule application
4. **Scoring**: Finding confidence and relevance scoring
5. **Forecast**: Asset score aggregation and trend analysis
6. **Seed Proposal**: Next iteration seed generation
7. **Blindspot Analysis**: Coverage gap identification
8. **BALLM**: Meta-layer generation with epistemic insights
9. **Scenario Synthesis**: Threat scenario generation
10. **Brief Synthesis**: Executive summary generation
11. **Export**: STIX bundle creation and file output

**PipelineOrchestrator**: Main coordination class
- Orchestrates the complete pipeline flow
- Handles error recovery and logging
- Manages configuration and state

### 4. Scoring Engine (`src/ngbse20/scoring/`)

**Scoring System**: Multi-dimensional scoring
- **Coverage**: Breadth of data collection
- **Recency**: Timeliness of findings
- **Confidence**: Reliability of sources and methods

### 5. BALLM Integration (`src/ngbse20/ballm/`)

**BALLMMetaLayerGenerator**: Epistemic analysis
- Generates meta-layer insights
- Provides epistemic humility scoring
- Identifies uncertainty sources
- Offers confidence intervals

### 6. Export Layer (`src/ngbse20/export/`)

**STIX Export**: Standardized threat intelligence
- Converts findings to STIX 2.1 format
- Creates STIX bundles for sharing
- Maintains provenance information

## Data Flow

```
Seeds → Collectors → Findings → Scoring → Asset Scores
  ↓         ↓           ↓         ↓          ↓
Rules → Validation → Rules → Blindspots → BALLM
  ↓         ↓           ↓         ↓          ↓
Config → Pipeline → Export → STIX → Reports
```

## Configuration Structure

### Main Configuration (`config/ngbse.config.yml`)
```yaml
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
```

### Rules Configuration (`config/rules.json`)
```json
[
  {
    "rule_id": "high_confidence_warning",
    "name": "High Confidence Finding",
    "condition": "finding.confidence > 0.9",
    "action": {
      "type": "warning_flag",
      "message": "High confidence finding detected"
    }
  }
]
```

### Seeds Configuration (`config/seeds.jsonl`)
```jsonl
{"id": "seed1", "type": "domain", "value": "example.com"}
{"id": "seed2", "type": "ip", "value": "1.2.3.4"}
```

## Security Considerations

### Credential Management
- All API keys stored in environment variables
- No credentials in configuration files
- Credential validation before collector activation

### Input Validation
- Seed validation and sanitization
- Rule condition validation
- Output sanitization for STIX export

### Error Handling
- Graceful degradation on collector failures
- Comprehensive logging and tracing
- Error recovery mechanisms

## Performance Characteristics

### Scalability
- Modular collector architecture allows easy addition of new sources
- Configurable collector enablement
- Parallel collection where possible

### Resource Usage
- Memory-efficient streaming for large datasets
- Configurable output directory management
- Optional LLM integration with fallback modes

## Extension Points

### Adding New Collectors
1. Implement `Collector` base class
2. Add to `CollectorManager.COLLECTOR_REGISTRY`
3. Implement credential validation
4. Add configuration options

### Adding New Pipeline Stages
1. Add method to `PipelineStages` class
2. Update orchestrator flow
3. Add appropriate tracing
4. Update tests

### Custom Scoring Algorithms
1. Extend scoring module
2. Update configuration schema
3. Add validation logic
4. Update documentation

## Monitoring and Observability

### Logging
- Structured logging with trace IDs
- Performance metrics collection
- Error tracking and alerting

### Tracing
- Pipeline stage execution tracking
- Performance bottleneck identification
- Debug information collection

### Metrics
- Collection success rates
- Scoring distribution analysis
- Pipeline execution times
- Resource utilization tracking