from __future__ import annotations

from typing import Any, List

from pydantic import BaseModel, Field, field_validator


class Seed(BaseModel):
    """Seed configuration for data collection."""

    id: str = Field(..., description="Unique identifier for the seed")
    query: str = Field(..., description="Query string or URL for collection")
    type: str = Field(
        "web",
        description=("Collector type (web, leakix, shodan, censys, urlscan, github, news)"),
    )
    asset_id: str | None = Field(None, description="Optional asset identifier")
    tags: list[str] = Field(default_factory=list, description="Tags for categorization")
    priority: int = Field(1, ge=1, le=10, description="Collection priority (1-10)")
    max_findings: int | None = Field(None, ge=1, description="Maximum findings to collect")

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        valid_types = ["web", "leakix", "shodan", "censys", "urlscan", "github", "news"]
        if v.lower() not in valid_types:
            raise ValueError(f"Invalid collector type. Must be one of: {', '.join(valid_types)}")
        return v.lower()

    @field_validator("tags", mode="before")
    @classmethod
    def _coerce_tags(cls, v: List[str] | None) -> List[str]:
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
    api_key: str | None = Field(None, description="API key for the collector")
    rate_limit: int | None = Field(None, ge=1, description="Rate limit per minute")
    timeout: int = Field(30, ge=1, description="Request timeout in seconds")
    max_retries: int = Field(3, ge=0, description="Maximum retry attempts")
    options: dict = Field(default_factory=dict, description="Collector-specific options")


class SourceTrustConfig(BaseModel):
    """Source trust configuration for scoring v18.1."""

    domains: dict[str, dict[str, Any]] = Field(default_factory=dict, description="Domain-specific trust levels")
    default_trust_level: float = Field(0.5, ge=0.0, le=1.0, description="Default trust level for unknown domains")

    @field_validator("domains")
    @classmethod
    def validate_domains(cls, v: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
        for domain, config in v.items():
            if "trust_level" not in config:
                raise ValueError(f"Domain {domain} missing trust_level")
            trust = config["trust_level"]
            if not isinstance(trust, (int, float)) or not 0.0 <= trust <= 1.0:
                raise ValueError(f"Domain {domain} trust_level must be 0.0-1.0, got {trust}")
        return v


class ExportConfig(BaseModel):
    """Export configuration for modular export system."""

    formats: list[str] = Field(default=["csv", "html", "docx"], description="List of export formats to generate")
    output_dir: str = Field("output", description="Output directory for exported files")
    csv_delimiter: str = Field(",", description="CSV delimiter character")
    csv_quote_char: str = Field('"', description="CSV quote character")
    csv_encoding: str = Field("utf-8", description="CSV file encoding")
    html_theme: str = Field("default", description="HTML report theme")
    html_title: str = Field("NGBSE 20.3 Security Analysis Report", description="HTML report title")
    html_template_path: str | None = Field(None, description="Custom HTML template path")
    docx_template_path: str | None = Field(None, description="Custom DOCX template path")
    include_charts: bool = Field(True, description="Include charts in HTML/DOCX reports")
    include_tables: bool = Field(True, description="Include tables in HTML/DOCX reports")
    stix_version: str = Field("2.1", description="STIX version for export")
    include_indicators: bool = Field(True, description="Include indicators in STIX export")
    include_observables: bool = Field(True, description="Include observables in STIX export")
    include_relationships: bool = Field(True, description="Include relationships in STIX export")

    @field_validator("formats")
    @classmethod
    def validate_formats(cls, v: list[str]) -> list[str]:
        valid_formats = ["csv", "html", "docx", "stix"]
        invalid_formats = [f for f in v if f not in valid_formats]
        if invalid_formats:
            raise ValueError(f"Invalid export formats: {invalid_formats}. Valid formats: {valid_formats}")
        return v

    @field_validator("stix_version")
    @classmethod
    def validate_stix_version(cls, v: str) -> str:
        valid_versions = ["2.0", "2.1"]
        if v not in valid_versions:
            raise ValueError(f"Invalid STIX version: {v}. Valid versions: {valid_versions}")
        return v


class CollectorManagerConfig(BaseModel):
    """Configuration for enhanced collector manager."""

    enabled_collectors: list[str] = Field(default_factory=list, description="List of enabled collector names")
    external_collectors: list[dict[str, str]] = Field(
        default_factory=list, description="External collector configurations"
    )
    auto_discovery: bool = Field(True, description="Enable automatic collector discovery")
    plugin_directory: str | None = Field(None, description="Directory for collector plugins")
    collector_timeout: int = Field(300, ge=1, description="Default collector timeout in seconds")
    max_concurrent_collectors: int = Field(5, ge=1, description="Maximum concurrent collectors")

    @field_validator("external_collectors")
    @classmethod
    def validate_external_collectors(cls, v: list[dict[str, str]]) -> list[dict[str, str]]:
        for collector in v:
            required_fields = ["name", "module_path", "class_name"]
            missing_fields = [f for f in required_fields if f not in collector]
            if missing_fields:
                raise ValueError(f"External collector missing required fields: {missing_fields}")
        return v


class Config(BaseModel):
    """Main configuration for NGBSE 20.3."""

    seeds: list[Seed] = Field(default_factory=list, description="List of seeds to process")
    rules: list[Rule] = Field(default_factory=list, description="List of rules to apply")
    collectors: list[CollectorConfig] = Field(default_factory=list, description="Collector configurations")
    options: dict[str, str] = Field(default_factory=dict, description="General options")
    source_trust: SourceTrustConfig | None = Field(None, description="Source trust configuration")

    # New modular configurations
    export: ExportConfig | None = Field(None, description="Export configuration")
    collector_manager: CollectorManagerConfig | None = Field(None, description="Collector manager configuration")

    # Pipeline options
    max_concurrent_collectors: int = Field(5, ge=1, description="Maximum concurrent collectors")
    output_format: str = Field("json", description="Output format (json, stix, docx)")
    enable_ballm: bool = Field(True, description="Enable BALLM meta-layer generation")
    enable_forecasting: bool = Field(True, description="Enable trend forecasting")
    enable_scenarios: bool = Field(True, description="Enable scenario synthesis")

    # Legacy fields for backward compatibility
    output_dir: str = Field("output", description="Output directory for results")
    allowlist: list[str] = Field(default_factory=list, description="Domain allowlist")

    @field_validator("output_format")
    @classmethod
    def validate_output_format(cls, v: str) -> str:
        valid_formats = ["json", "stix", "docx", "all"]
        if v.lower() not in valid_formats:
            raise ValueError(f"Invalid output format. Must be one of: {', '.join(valid_formats)}")
        return v.lower()

    def get_export_config(self) -> ExportConfig:
        """Get export configuration with defaults."""
        if self.export:
            return self.export
        return ExportConfig()

    def get_collector_manager_config(self) -> CollectorManagerConfig:
        """Get collector manager configuration with defaults."""
        if self.collector_manager:
            return self.collector_manager
        return CollectorManagerConfig()
