from __future__ import annotations

from typing import Optional, Dict, Any, List

from pydantic import BaseModel, Field, field_validator


class Seed(BaseModel):
    """Seed configuration for data collection."""

    id: str = Field(..., description="Unique identifier for the seed")
    query: str = Field(..., description="Query string or URL for collection")
    type: str = Field(
        "web",
        description=("Collector type (web, leakix, shodan, censys, urlscan, github, news)"),
    )
    asset_id: Optional[str] = Field(None, description="Optional asset identifier")
    tags: list[str] = Field(default_factory=list, description="Tags for categorization")
    priority: int = Field(1, ge=1, le=10, description="Collection priority (1-10)")
    max_findings: Optional[int] = Field(None, ge=1, description="Maximum findings to collect")

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        valid_types = ["web", "leakix", "shodan", "censys", "urlscan", "github", "news"]
        if v.lower() not in valid_types:
            raise ValueError(f"Invalid collector type. Must be one of: {', '.join(valid_types)}")
        return v.lower()

    @field_validator("tags", mode="before")
    @classmethod
    def _coerce_tags(cls, v: Optional[List[str]]) -> List[str]:
        return v or []


class Rule(BaseModel):
    """Rule configuration for data processing."""

    id: str = Field(..., description="Unique rule identifier")
    name: str = Field(..., description="Human-readable rule name")
    pattern: str = Field(..., description="Pattern or condition to match")
    weight: float = Field(1.0, ge=0, le=10, description="Rule weight (0-10)")
    action: dict = Field(default_factory=dict, description="Action to take when rule matches")
    enabled: bool = Field(True, description="Whether rule is active")
    tags: list[str] = Field(default_factory=list, description="Tags for categorization")

    @field_validator("action")
    @classmethod
    def validate_action(cls, v: dict) -> dict:
        valid_actions = ["warning_flag", "hard_block", "score_modifier", "tag_adder"]
        if "type" in v and v["type"] not in valid_actions:
            raise ValueError(f"Invalid action type. Must be one of: {', '.join(valid_actions)}")
        return v


class CollectorConfig(BaseModel):
    """Configuration for individual collectors."""

    name: str = Field(..., description="Collector name")
    enabled: bool = Field(True, description="Whether collector is enabled")
    api_key: Optional[str] = Field(None, description="API key for the collector")
    rate_limit: Optional[int] = Field(None, ge=1, description="Rate limit per minute")
    timeout: int = Field(30, ge=1, description="Request timeout in seconds")
    max_retries: int = Field(3, ge=0, description="Maximum retry attempts")
    options: dict = Field(default_factory=dict, description="Collector-specific options")


class LLMParams(BaseModel):
    """LLM parameters configuration."""
    
    temperature: float = Field(0.0, ge=0.0, le=2.0, description="Sampling temperature")
    top_p: float = Field(1.0, ge=0.0, le=1.0, description="Top-p sampling parameter")
    max_tokens: int = Field(400, ge=1, le=32000, description="Maximum tokens to generate")
    
    @field_validator("temperature")
    @classmethod
    def validate_temperature(cls, v: float) -> float:
        if v < 0.0 or v > 2.0:
            raise ValueError("Temperature must be between 0.0 and 2.0")
        return v


class LLMConfig(BaseModel):
    """LLM configuration for centralized model management."""
    
    provider: str = Field(..., description="LLM provider (openai, anthropic, mistral, ollama)")
    model: Optional[str] = Field(None, description="Specific model ID (optional, uses default if not set)")
    params: LLMParams = Field(default_factory=LLMParams, description="LLM parameters")
    seed: Optional[int] = Field(None, ge=0, description="Random seed for deterministic output")
    
    @field_validator("provider")
    @classmethod
    def validate_provider(cls, v: str) -> str:
        valid_providers = ["openai", "anthropic", "mistral", "ollama"]
        if v.lower() not in valid_providers:
            raise ValueError(f"Invalid provider. Must be one of: {', '.join(valid_providers)}")
        return v.lower()


class ProfileConfig(BaseModel):
    """Profile configuration for parameter overrides."""
    
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0, description="Override temperature")
    top_p: Optional[float] = Field(None, ge=0.0, le=1.0, description="Override top_p")
    max_tokens: Optional[int] = Field(None, ge=1, le=32000, description="Override max_tokens")


class SourceTrustConfig(BaseModel):
    """Source trust configuration for scoring v18.1."""
    
    domains: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict,
        description="Domain-specific trust levels"
    )
    default_trust_level: float = Field(
        0.5,
        ge=0.0,
        le=1.0,
        description="Default trust level for unknown domains"
    )
    
    @field_validator("domains")
    @classmethod
    def validate_domains(cls, v: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        for domain, config in v.items():
            if "trust_level" not in config:
                raise ValueError(f"Domain {domain} missing trust_level")
            trust = config["trust_level"]
            if not isinstance(trust, (int, float)) or not 0.0 <= trust <= 1.0:
                raise ValueError(f"Domain {domain} trust_level must be 0.0-1.0, got {trust}")
        return v


class Config(BaseModel):
    """Main configuration for NGBSE 20.2."""

    seeds: list[Seed] = Field(default_factory=list, description="List of seeds to process")
    rules: list[Rule] = Field(default_factory=list, description="List of rules to apply")
    collectors: list[CollectorConfig] = Field(default_factory=list, description="Collector configurations")
    options: dict[str, str] = Field(default_factory=dict, description="General options")
    source_trust: Optional[SourceTrustConfig] = Field(None, description="Source trust configuration")
    
    # LLM configuration
    llm: Optional[LLMConfig] = Field(None, description="LLM configuration")
    profiles: Dict[str, ProfileConfig] = Field(default_factory=dict, description="Named parameter profiles")

    # Pipeline options
    max_concurrent_collectors: int = Field(5, ge=1, description="Maximum concurrent collectors")
    output_format: str = Field("json", description="Output format (json, stix, docx)")
    enable_ballm: bool = Field(True, description="Enable BALLM meta-layer generation")
    enable_forecasting: bool = Field(True, description="Enable trend forecasting")
    enable_scenarios: bool = Field(True, description="Enable scenario synthesis")

    @field_validator("output_format")
    @classmethod
    def validate_output_format(cls, v: str) -> str:
        valid_formats = ["json", "stix", "docx", "all"]
        if v.lower() not in valid_formats:
            raise ValueError(f"Invalid output format. Must be one of: {', '.join(valid_formats)}")
        return v.lower()
