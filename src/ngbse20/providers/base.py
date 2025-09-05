"""
Base classes for LLM providers.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class LLMHandle:
    """Handle for LLM calls with bound parameters."""
    
    def __init__(self, provider: str, model: str, params: Dict[str, Any]):
        self.provider = provider
        self.model = model
        self.params = params
    
    def generate(self, system_prompt: str, user_prompt: str):
        """Generate response using the bound provider and parameters."""
        # This will be implemented by the specific provider
        raise NotImplementedError("Subclasses must implement generate method")


class BaseLLMProvider(ABC):
    """Base class for LLM providers."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
    
    @abstractmethod
    def list_models(self):
        """List available models for this provider."""
        pass
    
    @abstractmethod
    def default_model(self):
        """Get the default model for this provider."""
        pass
    
    @abstractmethod
    def bind(self, model: str, **params):
        """Bind a model and parameters to create an LLM handle."""
        pass