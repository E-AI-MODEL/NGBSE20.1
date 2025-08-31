# NGBSE 20.1

Simplified demonstration of the Next Generation Blind Spot Engine integrating real web collection, scoring, forecasting and seed proposal.

This repository contains a minimal Python package with a CLI entrypoint `ngbse20.cli:main`. The pipeline performs the following steps:

1. Validate rules against metrics
2. Collect web data for provided seeds using an allowlisted HTTP collector
3. Score findings
4. Aggregate asset scores and store history
5. Build a simple forecast using EWMA
6. Propose next seeds based on findings and asset risk
7. Export findings to a STIX 2.1 bundle

Run tests with `pytest` and view the package version with:

```bash
python -m ngbse20.cli --version
```
