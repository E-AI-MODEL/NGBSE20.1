#!/usr/bin/env python3
"""
LLM Factory Demo for NGBSE 20.2

Demonstrates the new centralized LLM management system with:
- Provider abstraction
- Centralized configuration
- Deterministic output
- JSON schema validation
- Audit trails
"""

import json
import os
from pathlib import Path

from src.ngbse20.llm_factory import build_llm, list_models, get_default_model
from src.ngbse20.config.models import LLMConfig, LLMParams, ProfileConfig
from src.ngbse20.config.loader import load_config
from src.ngbse20.utils.validation import validate_llm_output, BLINDSPOT_SCHEMA
from src.ngbse20.utils.prompt_hash import hash_prompt


def demo_basic_usage():
    """Demonstrate basic LLM factory usage."""
    print("=== Basic LLM Factory Usage ===")
    
    # Create LLM configuration
    config = LLMConfig(
        provider="openai",
        model="gpt-4o-mini",
        params=LLMParams(
            temperature=0.0,
            top_p=1.0,
            max_tokens=400
        ),
        seed=42
    )
    
    # Build LLM handle
    llm_handle = build_llm(config)
    print(f"Created LLM handle: {llm_handle.provider}/{llm_handle.model}")
    print(f"Parameters: {llm_handle.params}")
    
    # Generate response (mock for demo)
    system_prompt = "You are a helpful assistant."
    user_prompt = "What is 2+2?"
    
    # Generate hash for audit trail
    prompt_hash = hash_prompt(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        model=llm_handle.model,
        params=llm_handle.params,
        seed=config.seed
    )
    print(f"Prompt hash: {prompt_hash}")
    
    print()


def demo_profile_usage():
    """Demonstrate profile-based parameter overrides."""
    print("=== Profile-Based Configuration ===")
    
    # Base configuration
    config = LLMConfig(
        provider="anthropic",
        model="claude-3-5-sonnet-20241022",
        params=LLMParams(
            temperature=0.0,
            top_p=1.0,
            max_tokens=400
        ),
        seed=42
    )
    
    # Creative profile
    creative_profile = ProfileConfig(
        temperature=0.7,
        top_p=0.9,
        max_tokens=600
    )
    
    # Build with profile
    llm_handle = build_llm(config, creative_profile)
    print(f"Creative profile applied:")
    print(f"  Temperature: {llm_handle.params['temperature']}")
    print(f"  Top-p: {llm_handle.params['top_p']}")
    print(f"  Max tokens: {llm_handle.params['max_tokens']}")
    
    print()


def demo_environment_overrides():
    """Demonstrate environment variable overrides."""
    print("=== Environment Variable Overrides ===")
    
    # Set environment variables
    os.environ["NGBSE_LLM_PROVIDER"] = "mistral"
    os.environ["NGBSE_LLM_MODEL"] = "mistral-small-latest"
    os.environ["NGBSE_LLM_TEMPERATURE"] = "0.3"
    os.environ["NGBSE_LLM_MAX_TOKENS"] = "800"
    
    # Base configuration (will be overridden by env vars)
    config = LLMConfig(
        provider="openai",
        model="gpt-4o-mini",
        params=LLMParams(
            temperature=0.0,
            top_p=1.0,
            max_tokens=400
        ),
        seed=42
    )
    
    # Build with environment overrides
    llm_handle = build_llm(config)
    print(f"Environment overrides applied:")
    print(f"  Provider: {llm_handle.provider}")
    print(f"  Model: {llm_handle.model}")
    print(f"  Temperature: {llm_handle.params['temperature']}")
    print(f"  Max tokens: {llm_handle.params['max_tokens']}")
    
    # Clean up
    for key in ["NGBSE_LLM_PROVIDER", "NGBSE_LLM_MODEL", 
                "NGBSE_LLM_TEMPERATURE", "NGBSE_LLM_MAX_TOKENS"]:
        os.environ.pop(key, None)
    
    print()


def demo_provider_management():
    """Demonstrate provider management functionality."""
    print("=== Provider Management ===")
    
    providers = ["openai", "anthropic", "mistral", "ollama"]
    
    for provider in providers:
        try:
            models = list_models(provider)
            default = get_default_model(provider)
            print(f"{provider}:")
            print(f"  Default model: {default}")
            print(f"  Available models: {len(models)}")
            if models:
                print(f"  Sample models: {models[:3]}")
        except Exception as e:
            print(f"{provider}: Error - {e}")
        print()


def demo_validation():
    """Demonstrate JSON schema validation."""
    print("=== JSON Schema Validation ===")
    
    # Valid blindspot output
    valid_output = {
        "interpretation": "This represents a knowledge gap in threat intelligence coverage.",
        "epistemic_insights": [
            "Limited visibility into emerging threats",
            "Potential blind spots in monitoring"
        ],
        "confidence_level": 0.8
    }
    
    try:
        validated = validate_llm_output(json.dumps(valid_output), BLINDSPOT_SCHEMA)
        print("✓ Valid output passed validation")
        print(f"  Normalized output: {json.dumps(validated, indent=2)}")
    except Exception as e:
        print(f"✗ Validation failed: {e}")
    
    # Invalid output (missing required fields)
    invalid_output = {
        "interpretation": "This is incomplete."
    }
    
    try:
        validate_llm_output(json.dumps(invalid_output), BLINDSPOT_SCHEMA)
        print("✗ Invalid output should have failed validation")
    except Exception as e:
        print(f"✓ Invalid output correctly rejected: {e}")
    
    print()


def demo_config_loading():
    """Demonstrate configuration loading."""
    print("=== Configuration Loading ===")
    
    # Load configuration from file
    try:
        config = load_config("config/ngbse.config.yml")
        print("✓ Configuration loaded successfully")
        
        if config.llm:
            print(f"  LLM Provider: {config.llm.provider}")
            print(f"  LLM Model: {config.llm.model}")
            print(f"  Temperature: {config.llm.params.temperature}")
            print(f"  Seed: {config.llm.seed}")
        
        if config.profiles:
            print(f"  Profiles: {list(config.profiles.keys())}")
            for name, profile in config.profiles.items():
                print(f"    {name}: {profile.dict(exclude_none=True)}")
        
    except Exception as e:
        print(f"✗ Configuration loading failed: {e}")
    
    print()


def main():
    """Run all demonstrations."""
    print("NGBSE 20.2 LLM Factory Demo")
    print("=" * 50)
    print()
    
    demo_basic_usage()
    demo_profile_usage()
    demo_environment_overrides()
    demo_provider_management()
    demo_validation()
    demo_config_loading()
    
    print("Demo completed!")


if __name__ == "__main__":
    main()