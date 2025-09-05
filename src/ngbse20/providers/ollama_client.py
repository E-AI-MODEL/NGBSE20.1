"""
Ollama provider client for NGBSE 20.2.
"""

import os
from typing import Any, Dict, List, Optional

import requests
from requests.exceptions import RequestException

from .base import BaseLLMProvider, LLMHandle
from ..logging import get_logger

LOGGER = get_logger(__name__)


class OllamaClient(BaseLLMProvider):
    """Ollama provider client for local models."""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        super().__init__(api_key)
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        # Ollama doesn't require API key for local usage
        self.api_key = api_key
    
    def list_models(self) -> List[str]:
        """List available Ollama models."""
        try:
            return self._get_available_models()
        except Exception as e:
            LOGGER.warning(f"Failed to fetch Ollama models: {e}")
            # Return common models as fallback
            return [
                "llama3.2:latest",
                "llama3.1:latest", 
                "llama3:latest",
                "mistral:latest",
                "codellama:latest",
                "phi3:latest"
            ]
    
    def _get_available_models(self) -> List[str]:
        """Get available models from Ollama API."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=10)
            response.raise_for_status()
            
            data = response.json()
            models = []
            for model in data.get("models", []):
                models.append(model["name"])
            return models
        except Exception as e:
            LOGGER.warning(f"Failed to fetch models from Ollama: {e}")
            return [
                "llama3.2:latest",
                "llama3.1:latest",
                "llama3:latest", 
                "mistral:latest",
                "codellama:latest",
                "phi3:latest"
            ]
    
    def default_model(self) -> str:
        """Get default Ollama model."""
        return "llama3.2:latest"
    
    def bind(self, model: str, **params) -> "OllamaHandle":
        """Bind model and parameters."""
        return OllamaHandle(self, model, params)
    
    def _call_api(self, system_prompt: str, user_prompt: str,
                  model: str, temperature: float = 0.0,
                  top_p: float = 1.0, max_tokens: int = 400,
                  seed: Optional[int] = None) -> str:
        """Make API call to Ollama."""
        headers = {
            "Content-Type": "application/json"
        }
        
        # Combine system and user prompts for Ollama
        full_prompt = f"System: {system_prompt}\n\nUser: {user_prompt}"
        
        payload = {
            "model": model,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "top_p": top_p,
                "num_predict": max_tokens
            }
        }
        
        if seed is not None:
            payload["options"]["seed"] = seed
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                headers=headers,
                json=payload,
                timeout=120  # Ollama can be slower
            )
            response.raise_for_status()
            
            data = response.json()
            return data.get("response", "")
            
        except RequestException as e:
            LOGGER.error(f"Ollama API request failed: {e}")
            raise
        except KeyError as e:
            LOGGER.error(f"Unexpected Ollama API response format: {e}")
            raise


class OllamaHandle(LLMHandle):
    """Ollama-specific LLM handle."""
    
    def __init__(self, client: OllamaClient, model: str, params: Dict[str, Any]):
        super().__init__("ollama", model, params)
        self.client = client
    
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        """Generate response using Ollama API."""
        try:
            response = self.client._call_api(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                model=self.model,
                **self.params
            )
            return response
        except Exception as e:
            LOGGER.error(f"Ollama API call failed: {e}")
            raise


    def _call_api(self, system_prompt: str, user_prompt: str,
                  model: str, temperature: float = 0.0,
                  top_p: float = 1.0, max_tokens: int = 400,
                  seed: Optional[int] = None) -> str:
        """Make API call to Ollama."""
        headers = {
            "Content-Type": "application/json"
        }
        
        # Combine system and user prompts for Ollama
        full_prompt = f"System: {system_prompt}\n\nUser: {user_prompt}"
        
        payload = {
            "model": model,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "top_p": top_p,
                "num_predict": max_tokens
            }
        }
        
        if seed is not None:
            payload["options"]["seed"] = seed
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                headers=headers,
                json=payload,
                timeout=120  # Ollama can be slower
            )
            response.raise_for_status()
            
            data = response.json()
            return data.get("response", "")
            
        except RequestException as e:
            LOGGER.error(f"Ollama API request failed: {e}")
            raise
        except KeyError as e:
            LOGGER.error(f"Unexpected Ollama API response format: {e}")
            raise