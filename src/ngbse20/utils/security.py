"""
Security utilities for NGBSE 20.2.
Provides API key masking and security-related helper functions.
"""
import re
from typing import Any, Dict


def mask_api_key(api_key: str, visible_chars: int = 4) -> str:
    """
    Mask API key for safe logging.

    Args:
        api_key: The API key to mask
        visible_chars: Number of characters to show at the end (default: 4)

    Returns:
        Masked API key string
    """
    if not api_key or len(api_key) <= visible_chars:
        return "***"

    return "*" * (len(api_key) - visible_chars) + api_key[-visible_chars:]


def mask_credentials_in_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Mask credentials in a dictionary for safe logging.

    Args:
        data: Dictionary that may contain credentials

    Returns:
        Dictionary with masked credentials
    """
    masked_data = data.copy()

    # Common credential field names
    credential_fields = [
        'api_key', 'api_secret', 'token', 'password', 'secret',
        'access_token', 'refresh_token', 'private_key', 'auth_token'
    ]

    for key, value in masked_data.items():
        if isinstance(value, str) and any(cred_field in key.lower() for cred_field in credential_fields):
            masked_data[key] = mask_api_key(value)
        elif isinstance(value, dict):
            masked_data[key] = mask_credentials_in_dict(value)
        elif isinstance(value, list):
            masked_data[key] = [mask_credentials_in_dict(item) if isinstance(item, dict) else item for item in value]

    return masked_data


def mask_credentials_in_string(text: str) -> str:
    """
    Mask credentials in a string for safe logging.

    Args:
        text: String that may contain credentials

    Returns:
        String with masked credentials
    """
    # Pattern to match common API key formats
    patterns = [
        r'api[_-]?key["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_-]{8,})["\']?',
        r'token["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_-]{8,})["\']?',
        r'secret["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_-]{8,})["\']?',
        r'password["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_-]{8,})["\']?',
    ]

    masked_text = text
    for pattern in patterns:
        def replace_match(match):
            full_match = match.group(0)
            credential = match.group(1)
            masked_credential = mask_api_key(credential)
            return full_match.replace(credential, masked_credential)

        masked_text = re.sub(pattern, replace_match, masked_text, flags=re.IGNORECASE)

    return masked_text


def sanitize_error_message(error_msg: str, credentials: Dict[str, str] = None) -> str:
    """
    Sanitize error message by masking any credentials.

    Args:
        error_msg: Original error message
        credentials: Optional dictionary of credentials to mask

    Returns:
        Sanitized error message
    """
    # First, mask any credentials in the error message itself
    sanitized = mask_credentials_in_string(error_msg)

    # Then, if credentials dict is provided, mask those too
    if credentials:
        for key, value in credentials.items():
            if value and value in sanitized:
                sanitized = sanitized.replace(value, mask_api_key(value))

    return sanitized


def validate_api_key_format(api_key: str, expected_length: int = None) -> bool:
    """
    Validate API key format.

    Args:
        api_key: API key to validate
        expected_length: Expected length (optional)

    Returns:
        True if valid, False otherwise
    """
    if not api_key:
        return False

    # Basic validation - should be alphanumeric with some special chars
    if not re.match(r'^[a-zA-Z0-9_-]+$', api_key):
        return False

    # Length validation if specified
    if expected_length and len(api_key) != expected_length:
        return False

    # Minimum length check
    if len(api_key) < 8:
        return False

    return True
