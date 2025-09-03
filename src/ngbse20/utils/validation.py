"""
Input validation utilities for NGBSE 20.2.
Provides validation for user inputs to prevent security issues.
"""

import re
from typing import Any, List

from ..logging import get_logger

LOGGER = get_logger(__name__)


def validate_domain_name(domain: str) -> bool:
    """
    Validate domain name format.

    Args:
        domain: Domain name to validate

    Returns:
        True if valid, False otherwise
    """
    if not domain or domain == "*":
        return True  # Allow wildcard

    # Basic domain validation regex
    domain_pattern = (
        r"^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?"
        r"(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$"
    )

    # Check for suspicious patterns
    suspicious_patterns = [
        r"\.\.",  # Double dots
        r"^\.",  # Starts with dot
        r"\.$",  # Ends with dot
        r"\.-",  # Dot followed by dash
        r"-\.",  # Dash followed by dot
        r"--",  # Double dashes
    ]

    for pattern in suspicious_patterns:
        if re.search(pattern, domain):
            LOGGER.warning(f"Domain contains suspicious pattern '{pattern}': {domain}")
            return False

    return bool(re.match(domain_pattern, domain))


def validate_allowlist(allowlist: List[str]) -> List[str]:
    """
    Validate and sanitize allowlist domains.

    Args:
        allowlist: List of domain names

    Returns:
        Validated and sanitized allowlist

    Raises:
        ValueError: If invalid domains are found
    """
    if not allowlist:
        return ["*"]  # Default to allow all

    validated_domains = []
    invalid_domains = []

    for domain in allowlist:
        domain = domain.strip()
        if not domain:
            continue

        if validate_domain_name(domain):
            validated_domains.append(domain)
        else:
            invalid_domains.append(domain)

    if invalid_domains:
        error_msg = f"Invalid domains in allowlist: {', '.join(invalid_domains)}"
        LOGGER.error(error_msg)
        raise ValueError(error_msg)

    LOGGER.info(f"Allowlist validated: {len(validated_domains)} domains")
    return validated_domains


def validate_json_input(data: Any, expected_type: str = "object") -> bool:
    """
    Validate JSON input structure.

    Args:
        data: JSON data to validate
        expected_type: Expected type ("object", "array", "string")

    Returns:
        True if valid, False otherwise
    """
    if expected_type == "object" and not isinstance(data, dict):
        LOGGER.error(f"Expected object, got {type(data)}")
        return False
    elif expected_type == "array" and not isinstance(data, list):
        LOGGER.error(f"Expected array, got {type(data)}")
        return False
    elif expected_type == "string" and not isinstance(data, str):
        LOGGER.error(f"Expected string, got {type(data)}")
        return False

    return True


def sanitize_string_input(value: str, max_length: int = 1000) -> str:
    """
    Sanitize string input for safe processing.

    Args:
        value: String to sanitize
        max_length: Maximum allowed length

    Returns:
        Sanitized string
    """
    if not value:
        return ""

    # Remove null bytes and control characters
    sanitized = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", str(value))

    # Limit length
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
        LOGGER.warning(f"Input truncated to {max_length} characters")

    return sanitized
