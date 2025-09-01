"""
Configuration loader for NGBSE 20.2.
Centralizes configuration management and credential handling.
"""
import os
import json
from typing import Any, Dict, List, Optional
from pathlib import Path

from ..logging import get_logger

LOGGER = get_logger(__name__)


class ConfigLoader:
    """Centralized configuration loader with credential management."""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self._config_cache: Dict[str, Any] = {}
    
    def load_config(self, config_file: str = "ngbse.config.yml") -> Dict[str, Any]:
        """Load main configuration file."""
        config_path = self.config_dir / config_file
        
        if not config_path.exists():
            LOGGER.warning(f"Config file {config_path} not found, using defaults")
            return self._get_default_config()
        
        # For now, assume JSON format (can be extended to YAML later)
        if config_path.suffix == '.json':
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # Default to JSON for now
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    
    def load_rules(self, rules_file: str = "rules.json") -> List[Dict[str, Any]]:
        """Load rules configuration."""
        rules_path = self.config_dir / rules_file
        
        if not rules_path.exists():
            LOGGER.warning(f"Rules file {rules_path} not found, using empty rules")
            return []
        
        with open(rules_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def load_seeds(self, seeds_file: str = "seeds.jsonl") -> List[Dict[str, Any]]:
        """Load seeds configuration."""
        seeds_path = self.config_dir / seeds_file
        
        if not seeds_path.exists():
            LOGGER.warning(f"Seeds file {seeds_path} not found, using empty seeds")
            return []
        
        seeds = []
        with open(seeds_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    seeds.append(json.loads(line))
        
        return seeds
    
    def get_credentials(self) -> Dict[str, str]:
        """Extract credentials from environment variables."""
        credentials = {}
        
        # Common API key patterns
        api_keys = [
            'SHODAN_API_KEY',
            'CENSYS_API_ID', 'CENSYS_API_SECRET',
            'LEAKIX_API_KEY',
            'URLSCAN_API_KEY',
            'GITHUB_TOKEN',
            'NEWS_API_KEY',
            'OPENAI_API_KEY',
            'ANTHROPIC_API_KEY'
        ]
        
        for key in api_keys:
            value = os.getenv(key)
            if value:
                credentials[key] = value
        
        return credentials
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "output_dir": "out",
            "allowlist": ["*"],
            "collectors": {
                "enabled": ["http_web", "leakix", "shodan", "censys", "urlscan", "github", "news"]
            },
            "scoring": {
                "default_weights": {
                    "coverage": 0.3,
                    "recency": 0.3,
                    "confidence": 0.4
                }
            },
            "ballm": {
                "enabled": True,
                "model": "gpt-4"
            }
        }