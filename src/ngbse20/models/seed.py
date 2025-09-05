"""
Seed data models for NGBSE 20.3.
Provides Pydantic models for seed validation.
"""

import re
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


class Seed(BaseModel):
    """Seed model for validation."""

    id: str = Field(..., min_length=1, max_length=100, description="Unique seed identifier")
    query: str = Field(..., min_length=1, max_length=1000, description="Search query")
    type: str = Field(..., min_length=1, max_length=50, description="Seed type")

    # Optional fields
    priority: Optional[int] = Field(default=1, ge=1, le=10, description="Priority level (1-10)")
    metadata: Optional[dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")

    @field_validator("id")
    @classmethod
    def validate_id(cls, v: str) -> str:
        """Validate seed ID format."""
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError("Seed ID must contain only alphanumeric characters, " "underscores, and hyphens")
        return v

    @field_validator("query")
    @classmethod
    def validate_query(cls, v: str) -> str:
        """Validate query content."""
        if not v or not v.strip():
            raise ValueError("Query cannot be empty")

        # Check for suspicious patterns
        suspicious_patterns = [
            r"<script",  # Script injection
            r"javascript:",  # JavaScript protocol
            r"data:",  # Data protocol
            r"vbscript:",  # VBScript protocol
        ]

        for pattern in suspicious_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError(f"Query contains suspicious pattern: {pattern}")

        return v.strip()

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        """Validate seed type."""
        allowed_types = [
            "web",
            "shodan",
            "censys",
            "leakix",
            "urlscan",
            "github",
            "news",
            "infrastructure",
            "threat_intelligence",
            "data_breach",
            "code_repository",
            "network_intelligence",
        ]

        if v.lower() not in allowed_types:
            raise ValueError(f'Invalid seed type: {v}. Allowed types: {", ".join(allowed_types)}')

        return v.lower()

    @field_validator("metadata")
    @classmethod
    def validate_metadata(cls, v: Optional[dict[str, Any]]) -> dict[str, Any]:
        """Validate metadata structure."""
        if v is None:
            return {}

        # Limit metadata size
        if len(str(v)) > 5000:
            raise ValueError("Metadata too large (max 5000 characters)")

        return v

    model_config = {
        "extra": "forbid",  # Reject extra fields
        "validate_assignment": True,  # Validate on assignment
        "use_enum_values": True,  # Use enum values
    }
