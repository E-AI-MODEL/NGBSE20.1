"""
Prompt hashing utilities for caching and audit trails.
"""

import hashlib
import json
from typing import Any, Dict, Optional


def hash_prompt(system_prompt: str, user_prompt: str, 
                model: str, params: Dict[str, Any], 
                seed: Optional[int] = None):
    """
    Create a deterministic hash of a prompt and parameters.
    
    Args:
        system_prompt: System prompt text
        user_prompt: User prompt text
        model: Model identifier
        params: LLM parameters (temperature, top_p, max_tokens, etc.)
        seed: Random seed (optional)
        
    Returns:
        Hexadecimal hash string
    """
    # Create deterministic hash components
    components = {
        "system": system_prompt,
        "user": user_prompt,
        "model": model,
        "params": params,
    }
    
    if seed is not None:
        components["seed"] = seed
    
    # Sort keys for deterministic hashing
    hash_input = json.dumps(components, sort_keys=True, separators=(',', ':'))
    
    return hashlib.sha256(hash_input.encode('utf-8')).hexdigest()


def hash_input(input_data: Any):
    """
    Create a deterministic hash of input data.
    
    Args:
        input_data: Any serializable data
        
    Returns:
        Hexadecimal hash string
    """
    # Convert to JSON with sorted keys
    json_str = json.dumps(input_data, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(json_str.encode('utf-8')).hexdigest()