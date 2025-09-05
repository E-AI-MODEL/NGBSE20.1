"""
Configuration loader for NGBSE 20.2.
Centralizes configuration management and credential handling.
"""

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

import yaml
try:
    from pydantic import ValidationError
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    class ValidationError(Exception):
        pass

from ..logging import get_logger
from ..models.seed import Seed
from ..utils.validation import validate_allowlist
from .models import SourceTrustConfig, LLMConfig, ProfileConfig

LOGGER = get_logger(__name__)


@dataclass
class CollectorConfig:
    """Configuration for collectors."""

    enabled: List[str]
    rate_limits: Dict[str, int] = None


@dataclass
class ScoringConfig:
    """Configuration for scoring engine."""

    default_weights: Dict[str, float]


@dataclass
class BALLMConfig:
    """Configuration for BALLM."""

    enabled: bool = True
    model: str = "gpt-4"


@dataclass 
class NGBSEConfig:
    """Main NGBSE configuration schema."""

    output_dir: str = "out"
    llm: Optional[LLMConfig] = None
    profiles: Dict[str, ProfileConfig] = None
    allowlist: List[str] = None
    collectors: CollectorConfig = None
    scoring: ScoringConfig = None
    ballm: BALLMConfig = None

    def __post_init__(self):
        """Set defaults after initialization."""
        if self.allowlist is None:
            self.allowlist = ["*"]
        if self.collectors is None:
            self.collectors = CollectorConfig(enabled=["http_web", "shodan", "censys", "leakix"])
        if self.scoring is None:
            self.scoring = ScoringConfig(default_weights={"coverage": 0.3, "recency": 0.3, "confidence": 0.4})
        if self.ballm is None:
            self.ballm = BALLMConfig()


class ConfigLoader:
    """Centralized configuration loader with credential management."""

    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self._config_cache: Dict[str, Any] = {}

    def load_config(self, config_file: str = "ngbse.config.yml") -> NGBSEConfig:
        """Load main configuration file with validation."""
        config_path = self.config_dir / config_file

        if not config_path.exists():
            LOGGER.warning(f"Config file {config_path} not found, using defaults")
            return self._get_default_config()

        try:
            # Load based on file extension
            with open(config_path, "r", encoding="utf-8") as f:
                if config_path.suffix in [".yml", ".yaml"]:
                    raw_config = yaml.safe_load(f)
                elif config_path.suffix == ".json":
                    raw_config = json.load(f)
                else:
                    LOGGER.warning(f"Unknown config file format: {config_path.suffix}, trying YAML")
                    raw_config = yaml.safe_load(f)

            # Validate and convert to structured config
            return self._validate_and_convert_config(raw_config)

        except (FileNotFoundError, yaml.YAMLError, json.JSONDecodeError) as e:
            LOGGER.error(f"Failed to load config from {config_path}: {e}")
            LOGGER.info("Using default configuration")
            return self._get_default_config()
        except OSError as e:
            LOGGER.error(f"I/O error loading config from {config_path}: {e}")
            LOGGER.info("Using default configuration")
            return self._get_default_config()

    def load_rules(self, rules_file: str = "rules.json") -> List[Dict[str, Any]]:
        """Load rules configuration."""
        rules_path = self.config_dir / rules_file

        if not rules_path.exists():
            LOGGER.warning(f"Rules file {rules_path} not found, using empty rules")
            return []

        with open(rules_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def load_seeds(self, seeds_file: str = "seeds.jsonl") -> List[Dict[str, Any]]:
        """Load and validate seeds configuration."""
        seeds_path = self.config_dir / seeds_file

        if not seeds_path.exists():
            LOGGER.warning(f"Seeds file {seeds_path} not found, using empty seeds")
            return []

        seeds = []
        line_number = 0

        with open(seeds_path, "r", encoding="utf-8") as f:
            for line in f:
                line_number += 1
                line = line.strip()
                if line:
                    try:
                        # Parse JSON
                        raw_seed = json.loads(line)

                        # Validate with Pydantic
                        validated_seed = Seed(**raw_seed)
                        seeds.append(validated_seed.dict())

                    except json.JSONDecodeError as e:
                        LOGGER.error(f"Invalid JSON in seeds file at line {line_number}: {e}")
                        raise ValueError(f"Invalid JSON in seeds file at line {line_number}")
                    except (ValidationError, TypeError) as e:
                        LOGGER.error(f"Invalid seed data at line {line_number}: {e}")
                        raise ValueError(f"Invalid seed data at line {line_number}: {e}")

        LOGGER.info(f"Loaded and validated {len(seeds)} seeds")
        return seeds

    def get_credentials(self) -> Dict[str, str]:
        """Extract credentials from environment variables."""
        credentials = {}

        # Common API key patterns
        api_keys = [
            "SHODAN_API_KEY",
            "CENSYS_API_ID",
            "CENSYS_API_SECRET",
            "LEAKIX_API_KEY",
            "URLSCAN_API_KEY",
            "GITHUB_TOKEN",
            "NEWS_API_KEY",
            "OPENAI_API_KEY",
            "ANTHROPIC_API_KEY",
        ]

        for key in api_keys:
            value = os.getenv(key)
            if value:
                credentials[key] = value

        return credentials

    def _validate_and_convert_config(self, raw_config: Dict[str, Any]):
        """Validate and convert raw config to structured config."""
        try:
            # Validate required fields
            if not isinstance(raw_config, dict):
                raise ValueError("Configuration must be a dictionary")

            collectors = self._validate_collectors_config(raw_config)
            scoring = self._validate_scoring_config(raw_config)
            ballm = self._validate_ballm_config(raw_config)
            allowlist = self._validate_allowlist_config(raw_config)
            llm = self._validate_llm_config(raw_config)
            profiles = self._validate_profiles_config(raw_config)

            # Create main config
            config = NGBSEConfig(
                output_dir=raw_config.get("output_dir", "out"),
                allowlist=allowlist,
                collectors=collectors,
                scoring=scoring,
                ballm=ballm,
                llm=llm,
                profiles=profiles,
            )

            LOGGER.info("Configuration loaded and validated successfully")
            return config

        except (ValidationError, TypeError, KeyError) as e:
            LOGGER.error(f"Configuration validation failed: {e}")
            LOGGER.info("Using default configuration")
            return self._get_default_config()

    def _validate_collectors_config(self, raw_config: Dict[str, Any]):
        """Validate and convert collectors configuration."""
        collectors_config = raw_config.get("collectors", {})
        if not isinstance(collectors_config, dict):
            collectors_config = {"enabled": ["http_web", "shodan", "censys", "leakix"]}

        return CollectorConfig(
            enabled=collectors_config.get("enabled", ["http_web", "shodan", "censys", "leakix"]),
            rate_limits=collectors_config.get("rate_limits"),
        )

    def _validate_scoring_config(self, raw_config: Dict[str, Any]):
        """Validate and convert scoring configuration."""
        scoring_config = raw_config.get("scoring", {})
        if not isinstance(scoring_config, dict):
            scoring_config = {"default_weights": {"coverage": 0.3, "recency": 0.3, "confidence": 0.4}}

        return ScoringConfig(
            default_weights=scoring_config.get("default_weights", {"coverage": 0.3, "recency": 0.3, "confidence": 0.4})
        )

    def _validate_llm_config(self, raw_config: Dict[str, Any]):
        """Validate and convert LLM configuration."""
        llm_config = raw_config.get("llm")
        if not llm_config or not isinstance(llm_config, dict):
            return None
            
        try:
            return LLMConfig(**llm_config)
        except Exception as e:
            LOGGER.warning(f"Invalid LLM configuration: {e}")
            return None

    def _validate_profiles_config(self, raw_config: Dict[str, Any]):
        """Validate and convert profiles configuration."""
        profiles_config = raw_config.get("profiles", {})
        if not isinstance(profiles_config, dict):
            return {}
            
        profiles = {}
        for name, profile_data in profiles_config.items():
            if isinstance(profile_data, dict):
                try:
                    profiles[name] = ProfileConfig(**profile_data)
                except Exception as e:
                    LOGGER.warning(f"Invalid profile '{name}': {e}")
        return profiles

    def _validate_ballm_config(self, raw_config: Dict[str, Any]):
        """Validate and convert BALLM configuration."""
        ballm_config = raw_config.get("ballm", {})
        if not isinstance(ballm_config, dict):
            ballm_config = {"enabled": True, "model": "gpt-4"}

        return BALLMConfig(
            enabled=ballm_config.get("enabled", True),
            model=ballm_config.get("model", "gpt-4"),
        )

    def _validate_allowlist_config(self, raw_config: Dict[str, Any]):
        """Validate and convert allowlist configuration."""
        allowlist = raw_config.get("allowlist", ["*"])
        return validate_allowlist(allowlist)

    def _get_default_config(self):
        """Get default configuration."""
        return NGBSEConfig()


# Standalone functions for backward compatibility and easier imports
def load_config(config_file: str = "ngbse.config.yml", config_dir: str = "config"):
    """Load main configuration file with validation.

    Args:
        config_file: Name of the configuration file
        config_dir: Directory containing configuration files

    Returns:
        NGBSEConfig: Loaded and validated configuration
    """
    loader = ConfigLoader(config_dir)
    return loader.load_config(config_file)


def load_rules(rules_file: str = "rules.json", config_dir: str = "config") -> List[Dict[str, Any]]:
    """Load rules configuration.

    Args:
        rules_file: Name of the rules file
        config_dir: Directory containing configuration files

    Returns:
        List[Dict[str, Any]]: Loaded rules configuration
    """
    loader = ConfigLoader(config_dir)
    return loader.load_rules(rules_file)


def load_seeds(seeds_file: str = "seeds.jsonl", config_dir: str = "config") -> List[Dict[str, Any]]:
    """Load and validate seeds configuration.

    Args:
        seeds_file: Name of the seeds file
        config_dir: Directory containing configuration files

    Returns:
        List[Dict[str, Any]]: Loaded and validated seeds
    """
    loader = ConfigLoader(config_dir)
    return loader.load_seeds(seeds_file)


def validate_files(seeds_file: str, rules_file: str) -> tuple[int, int]:
    """Validate the syntax and structure of seed and rule files.

    Args:
        seeds_file: Path to the seeds file
        rules_file: Path to the rules file

    Returns:
        tuple[int, int]: Number of valid seeds and rules found

    Raises:
        FileNotFoundError: If files don't exist
        json.JSONDecodeError: If files contain invalid JSON
        ValueError: If validation fails
    """
    n_seeds = _validate_seeds_file(seeds_file)
    n_rules = _validate_rules_file(rules_file)

    LOGGER.info(f"Validation successful: {n_seeds} seeds and {n_rules} rules found")
    return n_seeds, n_rules


def _validate_seeds_file(seeds_file: str) -> int:
    """Validate seeds file and return count of valid seeds."""
    seeds_path = Path(seeds_file)

    if not seeds_path.exists():
        raise FileNotFoundError(f"Seeds file not found: {seeds_file}")

    n_seeds = 0
    line_number = 0

    with open(seeds_path, "r", encoding="utf-8") as f:
        for line in f:
            line_number += 1
            line = line.strip()
            if line:
                try:
                    # Parse JSON
                    raw_seed = json.loads(line)

                    # Validate with Pydantic
                    Seed(**raw_seed)
                    n_seeds += 1

                except json.JSONDecodeError as e:
                    raise json.JSONDecodeError(
                        f"Invalid JSON in seeds file at line {line_number}: {e}",
                        e.doc,
                        e.pos,
                    )
                except ValidationError as e:
                    raise ValueError(f"Invalid seed data at line {line_number}: {e}")

    return n_seeds


def _validate_rules_file(rules_file: str) -> int:
    """Validate rules file and return count of valid rules."""
    rules_path = Path(rules_file)

    if not rules_path.exists():
        raise FileNotFoundError(f"Rules file not found: {rules_file}")

    with open(rules_path, "r", encoding="utf-8") as f:
        try:
            rules_data = json.load(f)
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(f"Invalid JSON in rules file: {e}", e.doc, e.pos)

    if not isinstance(rules_data, list):
        raise ValueError("Rules file must contain a JSON array")

    n_rules = 0
    for i, rule_data in enumerate(rules_data):
        try:
            # Basic validation - check required fields
            if not isinstance(rule_data, dict):
                raise ValueError(f"Rule at index {i} must be a dictionary")

            required_fields = ["id", "name", "pattern"]
            for field in required_fields:
                if field not in rule_data:
                    raise ValueError(f"Rule at index {i} missing required field: {field}")

            n_rules += 1

        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid rule data at index {i}: {e}")

    return n_rules


def load_source_trust(sources_file: str = "sources.json", config_dir: str = "config") -> SourceTrustConfig:
    """Load source trust configuration.

    Args:
        sources_file: Name of the sources file
        config_dir: Directory containing configuration files

    Returns:
        SourceTrustConfig: Loaded and validated source trust configuration
    """
    sources_path = Path(config_dir) / sources_file

    if not sources_path.exists():
        LOGGER.warning(f"Sources file {sources_path} not found, using default trust config")
        return SourceTrustConfig()

    try:
        with open(sources_path, "r", encoding="utf-8") as f:
            raw_config = json.load(f)
        
        # Validate with Pydantic
        return SourceTrustConfig(**raw_config)
    
    except (FileNotFoundError, json.JSONDecodeError, ValidationError) as e:
        LOGGER.error(f"Failed to load source trust config from {sources_path}: {e}")
        LOGGER.info("Using default source trust configuration")
        return SourceTrustConfig()
