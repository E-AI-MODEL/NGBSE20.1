"""
Unit tests for ConfigLoader.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from src.ngbse20.config.loader import ConfigLoader


class TestConfigLoader:
    """Test cases for ConfigLoader."""

    def test_default_config(self):
        """Test default configuration loading."""
        loader = ConfigLoader()
        config = loader.load_config("nonexistent.json")

        assert config["output_dir"] == "out"
        assert config["allowlist"] == ["*"]
        assert "collectors" in config
        assert "scoring" in config

    def test_load_rules(self):
        """Test rules loading."""
        with tempfile.TemporaryDirectory() as temp_dir:
            rules_file = Path(temp_dir) / "rules.json"
            test_rules = [
                {"rule_id": "test1", "action": {"type": "warning"}},
                {"rule_id": "test2", "action": {"type": "hard_block"}},
            ]

            with open(rules_file, "w") as f:
                json.dump(test_rules, f)

            loader = ConfigLoader(temp_dir)
            rules = loader.load_rules("rules.json")

            assert len(rules) == 2
            assert rules[0]["rule_id"] == "test1"

    def test_load_seeds(self):
        """Test seeds loading."""
        with tempfile.TemporaryDirectory() as temp_dir:
            seeds_file = Path(temp_dir) / "seeds.jsonl"
            test_seeds = [
                {"id": "seed1", "type": "domain", "value": "example.com"},
                {"id": "seed2", "type": "ip", "value": "1.2.3.4"},
            ]

            with open(seeds_file, "w") as f:
                for seed in test_seeds:
                    f.write(json.dumps(seed) + "\n")

            loader = ConfigLoader(temp_dir)
            seeds = loader.load_seeds("seeds.jsonl")

            assert len(seeds) == 2
            assert seeds[0]["id"] == "seed1"

    @patch.dict(
        os.environ,
        {
            "SHODAN_API_KEY": "test_key",
            "CENSYS_API_ID": "test_id",
            "CENSYS_API_SECRET": "test_secret",
        },
    )
    def test_get_credentials(self):
        """Test credential extraction."""
        loader = ConfigLoader()
        credentials = loader.get_credentials()

        assert credentials["SHODAN_API_KEY"] == "test_key"
        assert credentials["CENSYS_API_ID"] == "test_id"
        assert credentials["CENSYS_API_SECRET"] == "test_secret"

    def test_load_nonexistent_files(self):
        """Test loading nonexistent files returns defaults/empty."""
        loader = ConfigLoader("nonexistent_dir")

        rules = loader.load_rules()
        seeds = loader.load_seeds()

        assert rules == []
        assert seeds == []
