# Scoring v18.1 - Source Trust and Keyword Scoring

## Overview

Scoring v18.1 introduces two new scoring components to enhance the accuracy and relevance of findings:

- **Source Trust Score (S_s)**: Evaluates the trustworthiness of findings based on their source domain
- **Keyword Score (S_k)**: Computes relevance based on pattern matching against configurable rules

## Features

### Source Trust Scoring

The source trust score evaluates findings based on the trustworthiness of their source domain:

- **Domain-based trust levels**: Configure trust levels for specific domains (0.0-1.0)
- **Default trust level**: Fallback trust level for unknown domains
- **URL extraction**: Automatically extracts domain from finding URLs

#### Configuration

Create `config/sources.json`:

```json
{
  "domains": {
    "github.com": {
      "trust_level": 0.9,
      "comment": "High trust - official GitHub"
    },
    "stackoverflow.com": {
      "trust_level": 0.8,
      "comment": "High trust - community verified"
    },
    "reddit.com": {
      "trust_level": 0.4,
      "comment": "Medium trust - user generated"
    }
  },
  "default_trust_level": 0.5
}
```

### Keyword Scoring

The keyword score evaluates findings based on pattern matching:

- **Configurable rules**: Define patterns with weights and actions
- **Multi-field search**: Searches across title, description, content, summary, and text fields
- **Normalized scoring**: Scores are normalized by `keyword_normalization_max` (default: 10.0)
- **Contributor tracking**: Tracks which rules contributed to the score

#### Configuration

Use existing `config/rules.json`:

```json
[
  {
    "id": "r1",
    "name": "Security Keywords",
    "pattern": "vulnerability|exploit|malware",
    "weight": 3.0,
    "enabled": true,
    "tags": ["security"]
  },
  {
    "id": "r2",
    "name": "Infrastructure Keywords",
    "pattern": "server|database|api",
    "weight": 2.0,
    "enabled": true,
    "tags": ["infrastructure"]
  }
]
```

## Usage

### Basic Usage

```python
from ngbse20.scoring.v18 import ScoringConfig, score_findings
from ngbse20.config.loader import load_source_trust, load_rules

# Load configurations
source_trust = load_source_trust()
rules = load_rules()

# Configure scoring
cfg = ScoringConfig(
    enable_source_trust=True,
    enable_keyword_score=True,
    w_source=0.25,      # Source trust weight
    w_keywords=0.15,    # Keyword score weight
    w_recency=0.60      # Recency weight
)

# Score findings
findings = [
    {
        "title": "Critical vulnerability found",
        "url": "https://github.com/security/repo",
        "timestamp": "2024-01-01T00:00:00Z"
    }
]

scored_findings = score_findings(findings, cfg, source_trust.dict(), rules)
```

### Shadow Mode

For gradual rollout, use shadow mode to compare old and new scoring:

```python
from ngbse20.scoring.shadow import score_findings_shadow, gradual_rollout_config

# Shadow mode - compute both scores for comparison
result, shadow_metrics = score_findings_shadow(
    findings, cfg, source_trust.dict(), rules, shadow_mode=True
)

print(f"Findings impacted: {shadow_metrics['findings_impacted']}")
print(f"Max score delta: {shadow_metrics['max_delta']:.3f}")
```

### Gradual Rollout

```python
# Stage 1: Shadow mode (no impact on scores)
cfg_shadow = gradual_rollout_config("shadow")

# Stage 2: Partial rollout (conservative weights)
cfg_partial = gradual_rollout_config("partial")

# Stage 3: Full rollout (recommended weights)
cfg_full = gradual_rollout_config("full")
```

## Configuration Flags

| Flag | Default | Description |
|------|---------|-------------|
| `enable_source_trust` | `False` | Enable source trust scoring |
| `enable_keyword_score` | `False` | Enable keyword pattern scoring |
| `w_source` | `0.25` | Weight for source trust score |
| `w_keywords` | `0.15` | Weight for keyword score |
| `w_recency` | `0.60` | Weight for recency score |
| `keyword_normalization_max` | `10.0` | Normalization factor for keyword scores |
| `scoring_version` | `"v18.1"` | Scoring version identifier |

## Output Format

### Enhanced Score Breakdown

```json
{
  "score": 0.85,
  "scoring_version": "v18.1",
  "score_breakdown": {
    "base": 0.75,
    "extras": 0.10,
    "recency": 0.80,
    "source_trust": 0.90,
    "keyword_score": 0.60,
    "keyword_raw": 6.0,
    "weights": {
      "w_source": 0.25,
      "w_keywords": 0.15,
      "w_recency": 0.60
    }
  },
  "contributors": [
    {
      "rule_id": "r1",
      "rule_name": "Security Keywords",
      "weight": 3.0,
      "matches": 2,
      "score": 6.0
    }
  ]
}
```

### Metrics

```json
{
  "_scoring_metrics": {
    "total_findings": 100,
    "source_trust_enabled": true,
    "keyword_score_enabled": true,
    "scoring_version": "v18.1",
    "source_trust_scores": [0.9, 0.8, 0.4, ...],
    "keyword_scores": [0.6, 0.3, 0.0, ...],
    "processing_time_ms": 45.2
  }
}
```

## Migration Guide

### From v18.0 to v18.1

1. **No breaking changes**: v18.1 is backward compatible
2. **Flags default to off**: New features are disabled by default
3. **Gradual rollout recommended**: Use shadow mode first

### Migration Steps

1. **Update configuration**:
   ```python
   # Add new flags to your scoring config
   cfg = ScoringConfig(
       enable_source_trust=False,  # Start disabled
       enable_keyword_score=False, # Start disabled
       # ... existing config
   )
   ```

2. **Create source trust config**:
   ```bash
   # Create config/sources.json with your domain trust levels
   ```

3. **Test in shadow mode**:
   ```python
   # Use shadow mode to compare old vs new scoring
   result, metrics = score_findings_shadow(findings, cfg, source_trust, rules)
   ```

4. **Gradual rollout**:
   ```python
   # Stage 1: Shadow mode
   cfg = gradual_rollout_config("shadow")
   
   # Stage 2: Partial rollout
   cfg = gradual_rollout_config("partial")
   
   # Stage 3: Full rollout
   cfg = gradual_rollout_config("full")
   ```

## Governance

### Configuration Management

- **CODEOWNERS**: `config/` directory requires review
- **Schema validation**: All config files validated on load
- **Git SHA tracking**: Config versions tracked in run metadata

### Best Practices

1. **Start with shadow mode**: Always test new scoring before enabling
2. **Monitor metrics**: Watch for score distribution changes
3. **Gradual rollout**: Use staged rollout approach
4. **Regular updates**: Keep source trust levels current

## Troubleshooting

### Common Issues

1. **Invalid trust levels**: Must be 0.0-1.0 range
2. **Invalid regex patterns**: Check rule patterns for syntax errors
3. **Missing config files**: Will fall back to defaults
4. **Performance issues**: Monitor processing time metrics

### Debug Mode

```python
import logging
logging.getLogger("ngbse20.scoring").setLevel(logging.DEBUG)

# Enable detailed logging
cfg = ScoringConfig(enable_source_trust=True, enable_keyword_score=True)
result = score_findings(findings, cfg, source_trust, rules)
```

## Performance

### Benchmarks

- **Small dataset** (< 100 findings): < 10ms
- **Medium dataset** (100-1000 findings): < 100ms  
- **Large dataset** (1000+ findings): < 1s

### Optimization Tips

1. **Precompile patterns**: Rules are compiled once per scoring run
2. **Limit contributors**: Only top 10 contributors are stored
3. **Cache domain lookups**: Source trust lookups are cached
4. **Monitor metrics**: Watch processing time in logs

## Examples

See `tests/test_scoring_v18_1.py` and `tests/integration/test_scoring_integration.py` for comprehensive examples.