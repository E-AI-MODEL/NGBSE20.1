from __future__ import annotations

from typing import Optional

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


class Config(BaseModel):
    """Main configuration for NGBSE 20.1."""

    seeds: list[Seed] = Field(default_factory=list, description="List of seeds to process")
    rules: list[Rule] = Field(default_factory=list, description="List of rules to apply")
    collectors: list[CollectorConfig] = Field(default_factory=list, description="Collector configurations")
    options: dict[str, str] = Field(default_factory=dict, description="General options")

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
