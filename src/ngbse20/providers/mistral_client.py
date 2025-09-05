"""
Mistral provider client for NGBSE 20.2.
"""

import os
from typing import Any, Dict, List, Optional

import requests
from requests.exceptions import RequestException

from .base import BaseLLMProvider, LLMHandle
from ..logging import get_logger

LOGGER = get_logger(__name__)


class MistralClient(BaseLLMProvider):
    """Mistral provider client."""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key)
        self.api_key = api_key or os.getenv("MISTRAL_API_KEY")
        if not self.api_key:
            raise ValueError("MISTRAL_API_KEY environment variable is required")
    
    def list_models(self):
        """List available Mistral models."""
        return [
            "mistral-large-latest",
            "mistral-medium-latest",
            "mistral-small-latest",
            "mistral-tiny-latest",
            "open-mistral-7b",
            "open-mixtral-8x7b",
            "open-mixtral-8x22b"
        ]
    
    def default_model(self):
        """Get default Mistral model."""
        return "mistral-small-latest"
    
    def bind(self, model: str, **params):
        """Bind model and parameters."""
        return MistralHandle(self, model, params)
    
    def _call_api(self, system_prompt: str, user_prompt: str,
                  model: str, temperature: float = 0.0,
                  top_p: float = 1.0, max_tokens: int = 400,
                  seed: Optional[int] = None):
        """Make API call to Mistral."""
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
            payload["random_seed"] = seed
        
        try:
            response = requests.post(
                "https://api.mistral.ai/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            
            data = response.json()
            return data["choices"][0]["message"]["content"]
            
        except RequestException as e:
            LOGGER.error(f"Mistral API request failed: {e}")
            raise
        except KeyError as e:
            LOGGER.error(f"Unexpected Mistral API response format: {e}")
            raise


class MistralHandle(LLMHandle):
    """Mistral-specific LLM handle."""
    
    def __init__(self, client: MistralClient, model: str, params: Dict[str, Any]):
        super().__init__("mistral", model, params)
        self.client = client
    
    def generate(self, system_prompt: str, user_prompt: str):
        """Generate response using Mistral API."""
        try:
            response = self.client._call_api(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                model=self.model,
                **self.params
            )
            return response
        except Exception as e:
            LOGGER.error(f"Mistral API call failed: {e}")
            raise


    def _call_api(self, system_prompt: str, user_prompt: str,
                  model: str, temperature: float = 0.0,
                  top_p: float = 1.0, max_tokens: int = 400,
                  seed: Optional[int] = None):
        """Make API call to Mistral."""
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
            payload["random_seed"] = seed
        
        try:
            response = requests.post(
                "https://api.mistral.ai/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            
            data = response.json()
            return data["choices"][0]["message"]["content"]
            
        except RequestException as e:
            LOGGER.error(f"Mistral API request failed: {e}")
            raise
        except KeyError as e:
            LOGGER.error(f"Unexpected Mistral API response format: {e}")
            raise