"""
Seed data models for NGBSE 20.2.
Provides Pydantic models for seed validation.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any
import re


class Seed(BaseModel):
    """Seed model for validation."""

    id: str = Field(
        ..., min_length=1, max_length=100, description="Unique seed identifier"
    )
    query: str = Field(..., min_length=1, max_length=1000, description="Search query")
    type: str = Field(..., min_length=1, max_length=50, description="Seed type")

    # Optional fields
    priority: Optional[int] = Field(
        default=1, ge=1, le=10, description="Priority level (1-10)"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Additional metadata"
    )

    @validator("id")
    def validate_id(cls, v):
        """Validate seed ID format."""
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError(
                "Seed ID must contain only alphanumeric characters, underscores, and hyphens"
            )
        return v

    @validator("query")
    def validate_query(cls, v):
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

    @validator("type")
    def validate_type(cls, v):
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
            raise ValueError(
                f'Invalid seed type: {v}. Allowed types: {", ".join(allowed_types)}'
            )

        return v.lower()

    @validator("metadata")
    def validate_metadata(cls, v):
        """Validate metadata structure."""
        if v is None:
            return {}

        # Limit metadata size
        if len(str(v)) > 5000:
            raise ValueError("Metadata too large (max 5000 characters)")

        return v

    class Config:
        """Pydantic configuration."""

        extra = "forbid"  # Reject extra fields
        validate_assignment = True  # Validate on assignment
        use_enum_values = True  # Use enum values
