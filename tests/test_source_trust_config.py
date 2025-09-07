"""Tests for source trust configuration validation."""

import json
from pathlib import Path

import pytest
from src.ngbse20.config.loader import load_source_trust
from src.ngbse20.config.models import SourceTrustConfig


class TestSourceTrustConfig:
    """Test source trust configuration model."""

    def test_valid_config(self):
        """Test valid source trust configuration."""
        config_data = {
            "domains": {
                "github.com": {"trust_level": 0.9, "comment": "High trust"},
                "stackoverflow.com": {"trust_level": 0.8, "comment": "Medium trust"},
            },
            "default_trust_level": 0.5,
        }

        config = SourceTrustConfig(**config_data)
        assert config.default_trust_level == 0.5
        assert "github.com" in config.domains
        assert config.domains["github.com"]["trust_level"] == 0.9

    def test_invalid_trust_level(self):
        """Test validation of trust level bounds."""
        with pytest.raises(ValueError, match="trust_level must be 0.0-1.0"):
            SourceTrustConfig(domains={"test.com": {"trust_level": 1.5}}, default_trust_level=0.5)

    def test_missing_trust_level(self):
        """Test validation of missing trust level."""
        with pytest.raises(ValueError, match="missing trust_level"):
            SourceTrustConfig(domains={"test.com": {"comment": "No trust level"}}, default_trust_level=0.5)

    def test_default_trust_level_bounds(self):
        """Test default trust level bounds validation."""
        with pytest.raises(ValueError, match="Input should be less than or equal to 1"):
            SourceTrustConfig(default_trust_level=1.5)

        with pytest.raises(ValueError, match="Input should be greater than or equal to 0"):
            SourceTrustConfig(default_trust_level=-0.1)


class TestSourceTrustLoader:
    """Test source trust configuration loading."""

    def test_load_valid_config(self, tmp_path):
        """Test loading valid source trust configuration."""
        config_data = {
            "domains": {"github.com": {"trust_level": 0.9, "comment": "High trust"}},
            "default_trust_level": 0.5,
        }

        config_file = tmp_path / "sources.json"
        with open(config_file, "w") as f:
            json.dump(config_data, f)

        config = load_source_trust("sources.json", str(tmp_path))
        assert config.default_trust_level == 0.5
        assert "github.com" in config.domains

    def test_load_missing_file(self, tmp_path):
        """Test loading when file is missing."""
        config = load_source_trust("nonexistent.json", str(tmp_path))
        assert config.default_trust_level == 0.5
        assert config.domains == {}

    def test_load_invalid_json(self, tmp_path):
        """Test loading invalid JSON file."""
        config_file = tmp_path / "sources.json"
        with open(config_file, "w") as f:
            f.write("invalid json")

        config = load_source_trust("sources.json", str(tmp_path))
        assert config.default_trust_level == 0.5
        assert config.domains == {}

    def test_load_invalid_schema(self, tmp_path):
        """Test loading configuration with invalid schema."""
        config_data = {"domains": {"test.com": {"trust_level": 1.5}}, "default_trust_level": 0.5}  # Invalid trust level

        config_file = tmp_path / "sources.json"
        with open(config_file, "w") as f:
            json.dump(config_data, f)

        config = load_source_trust("sources.json", str(tmp_path))
        # Should fall back to default config
        assert config.default_trust_level == 0.5
        assert config.domains == {}
