"""Integration tests for scoring v18.1."""

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
from src.ngbse20.config.loader import load_rules, load_source_trust
from src.ngbse20.scoring.v18 import ScoringConfig, score_findings


class TestScoringIntegration:
    """Integration tests for scoring system."""

    def test_end_to_end_scoring(self, tmp_path):
        """Test end-to-end scoring with real config files."""
        # Create test config files
        sources_config = {
            "domains": {
                "github.com": {"trust_level": 0.9, "comment": "High trust"},
                "stackoverflow.com": {"trust_level": 0.8, "comment": "Medium trust"},
                "reddit.com": {"trust_level": 0.4, "comment": "Low trust"},
            },
            "default_trust_level": 0.5,
        }

        rules_config = [
            {
                "id": "r1",
                "name": "Security Keywords",
                "pattern": "vulnerability|exploit|malware",
                "weight": 3.0,
                "enabled": True,
                "tags": ["security"],
            },
            {
                "id": "r2",
                "name": "Infrastructure Keywords",
                "pattern": "server|database|api",
                "weight": 2.0,
                "enabled": True,
                "tags": ["infrastructure"],
            },
        ]

        # Write config files
        sources_file = tmp_path / "sources.json"
        with open(sources_file, "w") as f:
            json.dump(sources_config, f)

        rules_file = tmp_path / "rules.json"
        with open(rules_file, "w") as f:
            json.dump(rules_config, f)

        # Load configurations
        source_trust = load_source_trust("sources.json", str(tmp_path))
        rules = load_rules("rules.json", str(tmp_path))

        # Create test findings
        findings = [
            {
                "title": "Critical vulnerability found in server",
                "description": "A serious security exploit was discovered",
                "url": "https://github.com/security/repo",
                "timestamp": "2024-01-01T00:00:00Z",
            },
            {
                "title": "Database optimization tips",
                "description": "How to improve API performance",
                "url": "https://stackoverflow.com/questions/123",
                "timestamp": "2024-01-02T00:00:00Z",
            },
            {
                "title": "Random discussion",
                "description": "Just some random content",
                "url": "https://reddit.com/r/random",
                "timestamp": "2024-01-03T00:00:00Z",
            },
        ]

        # Test with flags disabled (legacy mode)
        cfg_legacy = ScoringConfig(enable_source_trust=False, enable_keyword_score=False)

        result_legacy = score_findings(findings, cfg_legacy)
        assert len(result_legacy) == 3
        for finding in result_legacy:
            assert "score" in finding
            assert "scoring_version" in finding
            assert finding["scoring_version"] == "v18.1"

        # Test with flags enabled (new mode)
        cfg_new = ScoringConfig(
            enable_source_trust=True, enable_keyword_score=True, w_source=0.3, w_keywords=0.2, w_recency=0.5
        )

        result_new = score_findings(findings, cfg_new, source_trust.model_dump(), rules)
        assert len(result_new) == 3

        for finding in result_new:
            assert "score" in finding
            assert "score_breakdown" in finding
            assert "source_trust" in finding["score_breakdown"]
            assert "keyword_score" in finding["score_breakdown"]
            assert "contributors" in finding
            assert finding["scoring_version"] == "v18.1"

        # Verify GitHub finding has highest source trust
        github_finding = next(f for f in result_new if "github.com" in f["url"])
        assert github_finding["score_breakdown"]["source_trust"] == 0.9

        # Verify security keywords are detected
        security_finding = next(f for f in result_new if "vulnerability" in f["title"])
        assert len(security_finding["contributors"]) > 0
        assert any(c["rule_id"] == "r1" for c in security_finding["contributors"])

    def test_shadow_mode_comparison(self, tmp_path):
        """Test shadow mode - new scoring should not break existing behavior when flags off."""
        # Create minimal config
        sources_config = {"domains": {"github.com": {"trust_level": 0.9}}, "default_trust_level": 0.5}

        rules_config = [{"id": "r1", "name": "Test Rule", "pattern": "test", "weight": 1.0, "enabled": True}]

        # Write config files
        sources_file = tmp_path / "sources.json"
        with open(sources_file, "w") as f:
            json.dump(sources_config, f)

        rules_file = tmp_path / "rules.json"
        with open(rules_file, "w") as f:
            json.dump(rules_config, f)

        # Load configurations
        source_trust = load_source_trust("sources.json", str(tmp_path))
        rules = load_rules("rules.json", str(tmp_path))

        findings = [
            {
                "title": "Test finding",
                "url": "https://github.com/user/repo",
                "timestamp": "2024-01-01T00:00:00Z",
                "metrics": {"source": 0.5, "keywords": 0.3},
            }
        ]

        # Test legacy mode
        cfg_legacy = ScoringConfig(enable_source_trust=False, enable_keyword_score=False)

        result_legacy = score_findings(findings, cfg_legacy)

        # Test new mode with same weights as legacy
        cfg_new = ScoringConfig(
            enable_source_trust=False,
            enable_keyword_score=False,
            weights={"source": 0.3, "keywords": 0.3, "recency": 0.4},
        )

        result_new = score_findings(findings, cfg_new, source_trust.model_dump(), rules)

        # Scores should be identical when flags are off
        assert result_legacy[0]["score"] == result_new[0]["score"]

    def test_performance_with_large_dataset(self):
        """Test performance with larger dataset."""
        # Create large dataset
        findings = []
        for i in range(100):
            findings.append(
                {
                    "title": f"Finding {i} with security vulnerability",
                    "description": f"Description {i} about server and database",
                    "url": f"https://github.com/repo{i}",
                    "timestamp": "2024-01-01T00:00:00Z",
                }
            )

        rules = [
            {"id": f"r{i}", "name": f"Rule {i}", "pattern": f"pattern{i}|test{i}", "weight": 1.0, "enabled": True}
            for i in range(10)
        ]

        source_trust_config = {"domains": {"github.com": {"trust_level": 0.9}}, "default_trust_level": 0.5}

        cfg = ScoringConfig(enable_source_trust=True, enable_keyword_score=True)

        # Should complete without errors
        result = score_findings(findings, cfg, source_trust_config, rules)
        assert len(result) == 100

        # All scores should be bounded
        for finding in result:
            assert 0.0 <= finding["score"] <= 1.0
            assert 0.0 <= finding["score_breakdown"]["source_trust"] <= 1.0
            assert 0.0 <= finding["score_breakdown"]["keyword_score"] <= 1.0
