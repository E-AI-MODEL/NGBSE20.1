"""
Validation utilities for NGBSE 20.2.
Provides input validation, sanitization, and JSON schema validation.
"""

import hashlib
import json
import re
from typing import Any, Dict, List, Union

try:
    import jsonschema
except ImportError:
    jsonschema = None


def validate_and_normalize(obj: Dict[str, Any], schema: Dict[str, Any]):
    """
    Validate object against JSON schema and normalize for deterministic output.
    
    Args:
        obj: Object to validate and normalize
        schema: JSON schema for validation
        
    Returns:
        Normalized and validated object
        
    Raises:
        jsonschema.ValidationError: If object doesn't match schema
    """
    # Validate against schema
    if jsonschema is None:
        raise ImportError("jsonschema is required for validation")
    jsonschema.validate(instance=obj, schema=schema)
    
    # Normalize for deterministic output
    return _sort_object(obj)


def _sort_object(obj: Any):
    """
    Recursively sort object keys and lists for deterministic output.
    
    Args:
        obj: Object to sort
        
    Returns:
        Sorted object
    """
    if isinstance(obj, dict):
        return {k: _sort_object(v) for k in sorted(obj.keys())}
    elif isinstance(obj, list):
        try:
            # Try to sort list elements if they're comparable
            return sorted((_sort_object(item) for item in obj), 
                         key=lambda e: json.dumps(e, sort_keys=True))
        except TypeError:
            # If not comparable, just sort the items
            return [_sort_object(item) for item in obj]
    else:
        return obj


def create_hash(obj: Any):
    """
    Create a deterministic hash of an object.
    
    Args:
        obj: Object to hash
        
    Returns:
        Hexadecimal hash string
    """
    # Convert to JSON with sorted keys for deterministic hashing
    json_str = json.dumps(obj, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(json_str.encode('utf-8')).hexdigest()


def validate_llm_output(output: str, expected_schema: Dict[str, Any]):
    """
    Parse and validate LLM output against expected schema.
    
    Args:
        output: Raw LLM output string
        expected_schema: JSON schema for validation
        
    Returns:
        Parsed and validated output
        
    Raises:
        json.JSONDecodeError: If output is not valid JSON
        jsonschema.ValidationError: If output doesn't match schema
    """
    # Parse JSON
    try:
        parsed = json.loads(output)
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"LLM output is not valid JSON: {e.msg}", e.doc, e.pos)
    
    # Validate and normalize
    return validate_and_normalize(parsed, expected_schema)


# Common schemas for NGBSE modules
BLINDSPOT_SCHEMA = {
    "type": "object",
    "properties": {
        "interpretation": {"type": "string"},
        "epistemic_insights": {
            "type": "array",
            "items": {"type": "string"}
        },
        "confidence_level": {"type": "number", "minimum": 0, "maximum": 1}
    },
    "required": ["interpretation", "epistemic_insights", "confidence_level"],
    "additionalProperties": False
}

CURIOSITY_SCHEMA = {
    "type": "object",
    "properties": {
        "questions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "question": {"type": "string"},
                    "category": {"type": "string"},
                    "priority": {"type": "integer", "minimum": 1, "maximum": 10}
                },
                "required": ["question", "category", "priority"],
                "additionalProperties": False
            }
        }
    },
    "required": ["questions"],
    "additionalProperties": False
}

SCENARIO_SCHEMA = {
    "type": "object",
    "properties": {
        "future_scenario": {"type": "string"},
        "summary": {"type": "string"},
        "key_indicators": {
            "type": "array",
            "items": {"type": "string"}
        },
        "mitigation_strategies": {
            "type": "array",
            "items": {"type": "string"}
        }
    },
    "required": ["future_scenario", "summary", "key_indicators", "mitigation_strategies"],
    "additionalProperties": False
}

RISK_ANALYSIS_SCHEMA = {
    "type": "object",
    "properties": {
        "BLUF": {"type": "string"},
        "TopRisks": {
            "type": "array",
            "items": {"type": "string"}
        },
        "Actions": {
            "type": "array",
            "items": {"type": "string"}
        }
    },
    "required": ["BLUF", "TopRisks", "Actions"],
    "additionalProperties": False
}


# Legacy validation functions for backward compatibility
def sanitize_string_input(input_str: str, max_length: int = 1000):
    """
    Sanitize string input by removing dangerous characters and limiting length.
    
    Args:
        input_str: Input string to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized string
    """
    if not isinstance(input_str, str):
        return ""
    
    # Remove control characters and limit length
    sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', input_str)
    return sanitized[:max_length]


def validate_domain_name(domain: str):
    """
    Validate domain name format.
    
    Args:
        domain: Domain name to validate
        
    Returns:
        True if valid domain name
    """
    if not isinstance(domain, str):
        return False
    
    # Basic domain validation regex
    domain_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
    return bool(re.match(domain_pattern, domain))


def validate_json_input(json_str: str):
    """
    Validate if string is valid JSON.
    
    Args:
        json_str: String to validate as JSON
        
    Returns:
        True if valid JSON
    """
    if not isinstance(json_str, str):
        return False
    
    try:
        json.loads(json_str)
        return True
    except (json.JSONDecodeError, ValueError):
        return False


def validate_allowlist(allowlist: Union[str, List[str]]):
    """
    Validate and normalize allowlist configuration.
    
    Args:
        allowlist: Allowlist as string or list
        
    Returns:
        Normalized allowlist as list of strings
    """
    if isinstance(allowlist, str):
        if allowlist == "*":
            return ["*"]
        return [item.strip() for item in allowlist.split(",") if item.strip()]
    elif isinstance(allowlist, list):
        return [str(item).strip() for item in allowlist if str(item).strip()]
    else:
        return ["*"]