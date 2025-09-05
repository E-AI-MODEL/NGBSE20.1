"""
Anthropic provider client for NGBSE 20.2.
"""

import os
from typing import Any, Dict, List, Optional

import requests
from requests.exceptions import RequestException

from .base import BaseLLMProvider, LLMHandle
from ..logging import get_logger

LOGGER = get_logger(__name__)


class AnthropicClient(BaseLLMProvider):
    """Anthropic provider client."""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key)
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is required")
    
    def list_models(self):
        """List available Anthropic models."""
        return [
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022",
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307"
        ]
    
    def default_model(self):
        """Get default Anthropic model."""
        return "claude-3-5-sonnet-20241022"
    
    def bind(self, model: str, **params):
        """Bind model and parameters."""
        return AnthropicHandle(self, model, params)
    
    def _call_api(self, system_prompt: str, user_prompt: str,
                  model: str, temperature: float = 0.0,
                  top_p: float = 1.0, max_tokens: int = 400,
                  seed: Optional[int] = None):
        """Make API call to Anthropic."""
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}]
        }
        
        if seed is not None:
            payload["seed"] = seed
        
        try:
            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            
            data = response.json()
            parts = data.get("content", [])
            return "\n".join([p.get("text", "") for p in parts if p.get("type") == "text"])
            
        except RequestException as e:
            LOGGER.error(f"Anthropic API request failed: {e}")
            raise
        except KeyError as e:
            LOGGER.error(f"Unexpected Anthropic API response format: {e}")
            raise


class AnthropicHandle(LLMHandle):
    """Anthropic-specific LLM handle."""
    
    def __init__(self, client: AnthropicClient, model: str, params: Dict[str, Any]):
        super().__init__("anthropic", model, params)
        self.client = client
    
    def generate(self, system_prompt: str, user_prompt: str):
        """Generate response using Anthropic API."""
        try:
            response = self.client._call_api(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                model=self.model,
                **self.params
            )
            return response
        except Exception as e:
            LOGGER.error(f"Anthropic API call failed: {e}")
            raise


    def _call_api(self, system_prompt: str, user_prompt: str,
                  model: str, temperature: float = 0.0,
                  top_p: float = 1.0, max_tokens: int = 400,
                  seed: Optional[int] = None):
        """Make API call to Anthropic."""
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}]
        }
        
        if seed is not None:
            payload["seed"] = seed
        
        try:
            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            
            data = response.json()
            parts = data.get("content", [])
            return "\n".join([p.get("text", "") for p in parts if p.get("type") == "text"])
            
        except RequestException as e:
            LOGGER.error(f"Anthropic API request failed: {e}")
            raise
        except KeyError as e:
            LOGGER.error(f"Unexpected Anthropic API response format: {e}")
            raise