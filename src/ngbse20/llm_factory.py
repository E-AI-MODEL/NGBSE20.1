"""
LLM Factory for NGBSE 20.2.
Centralized LLM management with provider abstraction and configuration.
"""

import os
from typing import Any, Dict, List, Optional, Union

from .providers import OpenAIClient, AnthropicClient, MistralClient, OllamaClient
from .config.models import LLMConfig, ProfileConfig
from .utils.prompt_hash import hash_prompt
from .logging import get_logger

LOGGER = get_logger(__name__)


def get_provider_client(provider_name: str) -> Union[OpenAIClient, AnthropicClient, MistralClient, OllamaClient]:
    """
    Get provider client by name.
    
    Args:
        provider_name: Name of the provider (openai, anthropic, mistral, ollama)
        
    Returns:
        Provider client instance
        
    Raises:
        ValueError: If provider is not supported
    """
    provider_name = provider_name.lower()
    
    if provider_name == "openai":
        return OpenAIClient()
    elif provider_name == "anthropic":
        return AnthropicClient()
    elif provider_name == "mistral":
        return MistralClient()
    elif provider_name == "ollama":
        return OllamaClient()
    else:
        raise ValueError(f"Unsupported provider: {provider_name}")


def build_llm(config: LLMConfig, 
              profile: Optional[ProfileConfig] = None,
              overrides: Optional[Dict[str, Any]] = None,
              env: Optional[Dict[str, str]] = None) -> Any:
    """
    Build LLM handle from configuration.
    
    Args:
        config: LLM configuration
        profile: Optional profile to apply
        overrides: Optional parameter overrides
        env: Optional environment variables (defaults to os.environ)
        
    Returns:
        LLM handle for generation
        
    Raises:
        ValueError: If configuration is invalid
    """
    env = env or os.environ
    
    # Start with base config
    llm_config = {
        "provider": config.provider,
        "model": config.model,
        "params": config.params.dict(),
        "seed": config.seed
    }
    
    # Apply profile overrides
    if profile:
        profile_dict = profile.dict(exclude_none=True)
        if "params" in llm_config:
            llm_config["params"].update(profile_dict)
        else:
            llm_config["params"] = profile_dict
    
    # Apply manual overrides
    if overrides:
        if "params" in overrides:
            llm_config["params"].update(overrides["params"])
        llm_config.update({k: v for k, v in overrides.items() if k != "params"})
    
    # Apply environment variable overrides
    env_overrides = {
        "provider": env.get("NGBSE_LLM_PROVIDER"),
        "model": env.get("NGBSE_LLM_MODEL"),
        "params": {}
    }
    
    for env_key, param_key, cast_func in [
        ("NGBSE_LLM_TEMPERATURE", "temperature", float),
        ("NGBSE_LLM_TOP_P", "top_p", float),
        ("NGBSE_LLM_MAX_TOKENS", "max_tokens", int),
        ("NGBSE_LLM_SEED", "seed", int),
    ]:
        value = env.get(env_key)
        if value is not None:
            try:
                env_overrides["params"][param_key] = cast_func(value)
            except ValueError as e:
                LOGGER.warning(f"Invalid environment variable {env_key}: {e}")
    
    # Apply environment overrides
    if env_overrides["provider"]:
        llm_config["provider"] = env_overrides["provider"]
    if env_overrides["model"]:
        llm_config["model"] = env_overrides["model"]
    if env_overrides["params"]:
        llm_config["params"].update(env_overrides["params"])
    
    # Get provider client
    try:
        client = get_provider_client(llm_config["provider"])
    except ValueError as e:
        raise ValueError(f"Failed to initialize provider: {e}")
    
    # Validate model availability
    model = llm_config["model"]
    if model:
        available_models = client.list_models()
        if available_models and model not in available_models:
            LOGGER.warning(f"Model {model} not available for {llm_config['provider']}. Available: {available_models}")
            # Use default model instead
            model = client.default_model()
            LOGGER.info(f"Using default model: {model}")
    else:
        model = client.default_model()
        LOGGER.info(f"Using default model: {model}")
    
    # Create LLM handle
    params = llm_config["params"]
    handle = client.bind(model=model, **params)
    
    # Log configuration for audit trail
    LOGGER.info(f"LLM configured - Provider: {llm_config['provider']}, Model: {model}, Params: {params}")
    
    return handle


def list_models(provider: str) -> List[str]:
    """
    List available models for a provider.
    
    Args:
        provider: Provider name
        
    Returns:
        List of available model names
    """
    try:
        client = get_provider_client(provider)
        return client.list_models()
    except ValueError as e:
        LOGGER.error(f"Failed to list models for {provider}: {e}")
        return []


def get_default_model(provider: str) -> str:
    """
    Get default model for a provider.
    
    Args:
        provider: Provider name
        
    Returns:
        Default model name
    """
    try:
        client = get_provider_client(provider)
        return client.default_model()
    except ValueError as e:
        LOGGER.error(f"Failed to get default model for {provider}: {e}")
        return ""


def create_llm_handle(provider: str, model: Optional[str] = None, 
                     temperature: float = 0.0, top_p: float = 1.0,
                     max_tokens: int = 400, seed: Optional[int] = None) -> Any:
    """
    Create LLM handle with direct parameters (convenience method).
    
    Args:
        provider: Provider name
        model: Model name (optional, uses default if not provided)
        temperature: Sampling temperature
        top_p: Top-p sampling parameter
        max_tokens: Maximum tokens to generate
        seed: Random seed (optional)
        
    Returns:
        LLM handle
    """
    # Create minimal config
    from .config.models import LLMParams, LLMConfig
    
    params = LLMParams(
        temperature=temperature,
        top_p=top_p,
        max_tokens=max_tokens
    )
    
    config = LLMConfig(
        provider=provider,
        model=model,
        params=params,
        seed=seed
    )
    
    return build_llm(config)