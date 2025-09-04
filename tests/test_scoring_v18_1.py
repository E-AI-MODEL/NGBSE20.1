"""Tests for scoring v18.1 with source trust and keyword scoring."""

import pytest
from datetime import datetime, timezone
from src.ngbse20.scoring.v18 import (
    ScoringConfig, 
    score_findings, 
    _source_trust_score, 
    _keyword_pattern_score,
    _extract_domain
)


class TestSourceTrustScore:
    """Test source trust scoring functionality."""
    
    def test_extract_domain(self):
        """Test domain extraction from URLs."""
        assert _extract_domain("https://github.com/user/repo") == "github.com"
        assert _extract_domain("http://stackoverflow.com/questions/123") == "stackoverflow.com"
        assert _extract_domain("https://subdomain.example.com/path") == "subdomain.example.com"
        assert _extract_domain("invalid-url") is None
        assert _extract_domain("") is None
    
    def test_source_trust_score_with_config(self):
        """Test source trust scoring with configuration."""
        config = {
            "domains": {
                "github.com": {"trust_level": 0.9},
                "stackoverflow.com": {"trust_level": 0.8}
            },
            "default_trust_level": 0.5
        }
        
        finding = {"url": "https://github.com/user/repo"}
        assert _source_trust_score(finding, config) == 0.9
        
        finding = {"url": "https://stackoverflow.com/questions/123"}
        assert _source_trust_score(finding, config) == 0.8
        
        finding = {"url": "https://unknown.com/page"}
        assert _source_trust_score(finding, config) == 0.5
        
        finding = {"url": ""}
        assert _source_trust_score(finding, config) == 0.5
    
    def test_source_trust_score_no_config(self):
        """Test source trust scoring without configuration."""
        finding = {"url": "https://github.com/user/repo"}
        assert _source_trust_score(finding, None) == 0.0


class TestKeywordPatternScore:
    """Test keyword pattern scoring functionality."""
    
    def test_keyword_pattern_score_empty_rules(self):
        """Test keyword scoring with empty rules."""
        finding = {"title": "test content", "description": "test description"}
        score, contributors = _keyword_pattern_score(finding, [])
        assert score == 0.0
        assert contributors == []
    
    def test_keyword_pattern_score_with_rules(self):
        """Test keyword scoring with rules."""
        rules = [
            {
                "id": "r1",
                "name": "Test Rule",
                "pattern": "test",
                "weight": 2.0,
                "enabled": True
            },
            {
                "id": "r2", 
                "name": "Security Rule",
                "pattern": "security|vulnerability",
                "weight": 3.0,
                "enabled": True
            }
        ]
        
        finding = {
            "title": "Test security vulnerability found",
            "description": "This is a test case for security testing"
        }
        
        score, contributors = _keyword_pattern_score(finding, rules)
        assert score > 0
        assert len(contributors) == 2
        assert contributors[0]["rule_id"] in ["r1", "r2"]
        assert contributors[0]["matches"] > 0
    
    def test_keyword_pattern_score_disabled_rule(self):
        """Test keyword scoring with disabled rules."""
        rules = [
            {
                "id": "r1",
                "name": "Disabled Rule",
                "pattern": "test",
                "weight": 2.0,
                "enabled": False
            }
        ]
        
        finding = {"title": "test content"}
        score, contributors = _keyword_pattern_score(finding, rules)
        assert score == 0.0
        assert contributors == []
    
    def test_keyword_pattern_score_invalid_regex(self):
        """Test keyword scoring with invalid regex patterns."""
        rules = [
            {
                "id": "r1",
                "name": "Invalid Rule",
                "pattern": "[invalid",
                "weight": 2.0,
                "enabled": True
            }
        ]
        
        finding = {"title": "test content"}
        score, contributors = _keyword_pattern_score(finding, rules)
        assert score == 0.0
        assert contributors == []


class TestScoringIntegration:
    """Test integrated scoring functionality."""
    
    def test_legacy_scoring_unchanged(self):
        """Test that legacy scoring remains unchanged when flags are off."""
        cfg = ScoringConfig(
            enable_source_trust=False,
            enable_keyword_score=False
        )
        
        findings = [
            {
                "title": "Test finding",
                "timestamp": "2024-01-01T00:00:00Z",
                "metrics": {"source": 0.5, "keywords": 0.3}
            }
        ]
        
        result = score_findings(findings, cfg)
        assert len(result) == 1
        assert "score" in result[0]
        assert "scoring_version" in result[0]
        assert result[0]["scoring_version"] == "v18.1"
    
    def test_new_scoring_with_flags(self):
        """Test new scoring with flags enabled."""
        cfg = ScoringConfig(
            enable_source_trust=True,
            enable_keyword_score=True,
            w_source=0.3,
            w_keywords=0.2,
            w_recency=0.5
        )
        
        source_trust_config = {
            "domains": {"github.com": {"trust_level": 0.9}},
            "default_trust_level": 0.5
        }
        
        rules = [
            {
                "id": "r1",
                "name": "Test Rule",
                "pattern": "test",
                "weight": 1.0,
                "enabled": True
            }
        ]
        
        findings = [
            {
                "title": "Test finding",
                "url": "https://github.com/user/repo",
                "timestamp": "2024-01-01T00:00:00Z"
            }
        ]
        
        result = score_findings(findings, cfg, source_trust_config, rules)
        assert len(result) == 1
        assert "score_breakdown" in result[0]
        assert "source_trust" in result[0]["score_breakdown"]
        assert "keyword_score" in result[0]["score_breakdown"]
        assert "contributors" in result[0]
    
    def test_scoring_deterministic(self):
        """Test that scoring is deterministic."""
        cfg = ScoringConfig(
            enable_source_trust=True,
            enable_keyword_score=True
        )
        
        source_trust_config = {
            "domains": {"github.com": {"trust_level": 0.9}},
            "default_trust_level": 0.5
        }
        
        rules = [
            {
                "id": "r1",
                "name": "Test Rule",
                "pattern": "test",
                "weight": 1.0,
                "enabled": True
            }
        ]
        
        findings = [
            {
                "title": "Test finding",
                "url": "https://github.com/user/repo",
                "timestamp": "2024-01-01T00:00:00Z"
            }
        ]
        
        result1 = score_findings(findings, cfg, source_trust_config, rules)
        result2 = score_findings(findings, cfg, source_trust_config, rules)
        
        assert result1[0]["score"] == result2[0]["score"]
        assert result1[0]["score_breakdown"] == result2[0]["score_breakdown"]
    
    def test_score_bounds(self):
        """Test that all scores are within [0, 1] bounds."""
        cfg = ScoringConfig(
            enable_source_trust=True,
            enable_keyword_score=True
        )
        
        source_trust_config = {
            "domains": {"github.com": {"trust_level": 1.5}},  # Test clamping
            "default_trust_level": 0.5
        }
        
        rules = [
            {
                "id": "r1",
                "name": "High Weight Rule",
                "pattern": "test",
                "weight": 100.0,  # Test normalization
                "enabled": True
            }
        ]
        
        findings = [
            {
                "title": "test test test",  # Multiple matches
                "url": "https://github.com/user/repo",
                "timestamp": "2024-01-01T00:00:00Z"
            }
        ]
        
        result = score_findings(findings, cfg, source_trust_config, rules)
        assert 0.0 <= result[0]["score"] <= 1.0
        assert 0.0 <= result[0]["score_breakdown"]["source_trust"] <= 1.0
        assert 0.0 <= result[0]["score_breakdown"]["keyword_score"] <= 1.0


class TestScoringConfig:
    """Test scoring configuration."""
    
    def test_default_config(self):
        """Test default configuration values."""
        cfg = ScoringConfig()
        assert cfg.enable_source_trust is False
        assert cfg.enable_keyword_score is False
        assert cfg.w_source == 0.25
        assert cfg.w_keywords == 0.15
        assert cfg.w_recency == 0.60
        assert cfg.keyword_normalization_max == 10.0
        assert cfg.scoring_version == "v18.1"
    
    def test_config_validation(self):
        """Test configuration validation."""
        # Test valid config
        cfg = ScoringConfig(
            enable_source_trust=True,
            enable_keyword_score=True,
            w_source=0.3,
            w_keywords=0.2,
            w_recency=0.5
        )
        assert cfg.w_source == 0.3
        assert cfg.w_keywords == 0.2
        assert cfg.w_recency == 0.5