"""
OpenAI provider client for NGBSE 20.2.
"""

import os
from typing import Any, Dict, List, Optional

import requests
from requests.exceptions import RequestException

from .base import BaseLLMProvider, LLMHandle
from ..logging import get_logger

LOGGER = get_logger(__name__)


class OpenAIClient(BaseLLMProvider):
    """OpenAI provider client."""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key)
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
    
    def list_models(self) -> List[str]:
        """List available OpenAI models."""
        try:
            # Cache models for 1 hour
            return self._get_cached_models()
        except Exception as e:
            LOGGER.warning(f"Failed to fetch OpenAI models: {e}")
            # Return known models as fallback
            return [
                "gpt-4o",
                "gpt-4o-mini", 
                "gpt-4-turbo",
                "gpt-4",
                "gpt-3.5-turbo",
                "o1-preview",
                "o1-mini"
            ]
    
    def _get_cached_models(self) -> List[str]:
        """Get cached models or fetch from API."""
        # In a real implementation, this would use a proper cache
        # For now, return the known models
        return [
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-turbo", 
            "gpt-4",
            "gpt-3.5-turbo",
            "o1-preview",
            "o1-mini"
        ]
    
    def default_model(self) -> str:
        """Get default OpenAI model."""
        return "gpt-4o-mini"
    
    def bind(self, model: str, **params) -> "OpenAIHandle":
        """Bind model and parameters."""
        return OpenAIHandle(self, model, params)


class OpenAIHandle(LLMHandle):
    """OpenAI-specific LLM handle."""
    
    def __init__(self, client: OpenAIClient, model: str, params: Dict[str, Any]):
        super().__init__("openai", model, params)
        self.client = client
    
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """Generate response using OpenAI API."""
        try:
            response = self.client._call_api(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                model=self.model,
                **self.params
            )
            return response
        except Exception as e:
            LOGGER.error(f"OpenAI API call failed: {e}")
            raise


class OpenAIClient:
    """OpenAI provider client with API implementation."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
    
    def list_models(self) -> List[str]:
        """List available OpenAI models."""
        try:
            return self._get_cached_models()
        except Exception as e:
            LOGGER.warning(f"Failed to fetch OpenAI models: {e}")
            return [
                "gpt-4o",
                "gpt-4o-mini",
                "gpt-4-turbo",
                "gpt-4",
                "gpt-3.5-turbo",
                "o1-preview",
                "o1-mini"
            ]
    
    def _get_cached_models(self) -> List[str]:
        """Get cached models."""
        return [
            "gpt-4o",
            "gpt-4o-mini", 
            "gpt-4-turbo",
            "gpt-4",
            "gpt-3.5-turbo",
            "o1-preview",
            "o1-mini"
        ]
    
    def default_model(self) -> str:
        """Get default model."""
        return "gpt-4o-mini"
    
    def bind(self, model: str, **params) -> "OpenAIHandle":
        """Bind model and parameters."""
        return OpenAIHandle(self, model, params)
    
    def _call_api(self, system_prompt: str, user_prompt: str, 
                  model: str, temperature: float = 0.0, 
                  top_p: float = 1.0, max_tokens: int = 400,
                  seed: Optional[int] = None) -> str:
        """Make API call to OpenAI."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": temperature,
            "top_p": top_p,
            "max_tokens": max_tokens
        }
        
        if seed is not None:
            payload["seed"] = seed
        
        try:
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            
            data = response.json()
            return data["choices"][0]["message"]["content"]
            
        except RequestException as e:
            LOGGER.error(f"OpenAI API request failed: {e}")
            raise
        except KeyError as e:
            LOGGER.error(f"Unexpected OpenAI API response format: {e}")
            raise