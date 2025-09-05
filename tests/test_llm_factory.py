"""
Tests for LLM Factory functionality.
"""

import pytest
from unittest.mock import Mock, patch

from src.ngbse20.llm_factory import build_llm, list_models, get_default_model, get_provider_client
from src.ngbse20.config.models import LLMConfig, LLMParams, ProfileConfig


class TestLLMFactory:
    """Test LLM Factory functionality."""
    
    def test_get_provider_client_openai(self):
        """Test OpenAI provider client creation."""
        with patch('src.ngbse20.llm_factory.OpenAIClient') as mock_client:
            mock_client.return_value = Mock()
            client = get_provider_client("openai")
            mock_client.assert_called_once()
    
    def test_get_provider_client_anthropic(self):
        """Test Anthropic provider client creation."""
        with patch('src.ngbse20.llm_factory.AnthropicClient') as mock_client:
            mock_client.return_value = Mock()
            client = get_provider_client("anthropic")
            mock_client.assert_called_once()
    
    def test_get_provider_client_mistral(self):
        """Test Mistral provider client creation."""
        with patch('src.ngbse20.llm_factory.MistralClient') as mock_client:
            mock_client.return_value = Mock()
            client = get_provider_client("mistral")
            mock_client.assert_called_once()
    
    def test_get_provider_client_ollama(self):
        """Test Ollama provider client creation."""
        with patch('src.ngbse20.llm_factory.OllamaClient') as mock_client:
            mock_client.return_value = Mock()
            client = get_provider_client("ollama")
            mock_client.assert_called_once()
    
    def test_get_provider_client_invalid(self):
        """Test invalid provider raises error."""
        with pytest.raises(ValueError, match="Unsupported provider"):
            get_provider_client("invalid")
    
    def test_build_llm_basic(self):
        """Test basic LLM build."""
        config = LLMConfig(
            provider="openai",
            model="gpt-4o-mini",
            params=LLMParams(temperature=0.0, top_p=1.0, max_tokens=400),
            seed=42
        )
        
        with patch('src.ngbse20.llm_factory.get_provider_client') as mock_get_client:
            mock_client = Mock()
            mock_handle = Mock()
            mock_client.list_models.return_value = ["gpt-4o-mini"]
            mock_client.default_model.return_value = "gpt-4o-mini"
            mock_client.bind.return_value = mock_handle
            mock_get_client.return_value = mock_client
            
            handle = build_llm(config)
            
            mock_get_client.assert_called_once_with("openai")
            mock_client.bind.assert_called_once()
            assert handle == mock_handle
    
    def test_build_llm_with_profile(self):
        """Test LLM build with profile overrides."""
        config = LLMConfig(
            provider="openai",
            model="gpt-4o-mini",
            params=LLMParams(temperature=0.0, top_p=1.0, max_tokens=400),
            seed=42
        )
        
        profile = ProfileConfig(temperature=0.7, max_tokens=600)
        
        with patch('src.ngbse20.llm_factory.get_provider_client') as mock_get_client:
            mock_client = Mock()
            mock_handle = Mock()
            mock_client.list_models.return_value = ["gpt-4o-mini"]
            mock_client.default_model.return_value = "gpt-4o-mini"
            mock_client.bind.return_value = mock_handle
            mock_get_client.return_value = mock_client
            
            handle = build_llm(config, profile)
            
            # Check that bind was called with profile overrides
            call_args = mock_client.bind.call_args
            assert call_args[1]["temperature"] == 0.7
            assert call_args[1]["max_tokens"] == 600
            assert call_args[1]["top_p"] == 1.0  # From original config
    
    def test_build_llm_with_env_overrides(self):
        """Test LLM build with environment variable overrides."""
        config = LLMConfig(
            provider="openai",
            model="gpt-4o-mini",
            params=LLMParams(temperature=0.0, top_p=1.0, max_tokens=400),
            seed=42
        )
        
        env_overrides = {
            "NGBSE_LLM_PROVIDER": "anthropic",
            "NGBSE_LLM_MODEL": "claude-3-5-sonnet-20241022",
            "NGBSE_LLM_TEMPERATURE": "0.5",
            "NGBSE_LLM_MAX_TOKENS": "800"
        }
        
        with patch('src.ngbse20.llm_factory.get_provider_client') as mock_get_client:
            mock_client = Mock()
            mock_handle = Mock()
            mock_client.list_models.return_value = ["claude-3-5-sonnet-20241022"]
            mock_client.default_model.return_value = "claude-3-5-sonnet-20241022"
            mock_client.bind.return_value = mock_handle
            mock_get_client.return_value = mock_client
            
            handle = build_llm(config, env=env_overrides)
            
            # Should call with anthropic provider due to env override
            mock_get_client.assert_called_once_with("anthropic")
            
            # Check that bind was called with env overrides
            call_args = mock_client.bind.call_args
            assert call_args[1]["temperature"] == 0.5
            assert call_args[1]["max_tokens"] == 800
    
    def test_list_models(self):
        """Test list models functionality."""
        with patch('src.ngbse20.llm_factory.get_provider_client') as mock_get_client:
            mock_client = Mock()
            mock_client.list_models.return_value = ["gpt-4o", "gpt-4o-mini"]
            mock_get_client.return_value = mock_client
            
            models = list_models("openai")
            
            assert models == ["gpt-4o", "gpt-4o-mini"]
            mock_get_client.assert_called_once_with("openai")
    
    def test_get_default_model(self):
        """Test get default model functionality."""
        with patch('src.ngbse20.llm_factory.get_provider_client') as mock_get_client:
            mock_client = Mock()
            mock_client.default_model.return_value = "gpt-4o-mini"
            mock_get_client.return_value = mock_client
            
            model = get_default_model("openai")
            
            assert model == "gpt-4o-mini"
            mock_get_client.assert_called_once_with("openai")
    
    def test_model_validation_fallback(self):
        """Test model validation with fallback to default."""
        config = LLMConfig(
            provider="openai",
            model="invalid-model",
            params=LLMParams(temperature=0.0, top_p=1.0, max_tokens=400),
            seed=42
        )
        
        with patch('src.ngbse20.llm_factory.get_provider_client') as mock_get_client:
            mock_client = Mock()
            mock_handle = Mock()
            mock_client.list_models.return_value = ["gpt-4o-mini"]
            mock_client.default_model.return_value = "gpt-4o-mini"
            mock_client.bind.return_value = mock_handle
            mock_get_client.return_value = mock_client
            
            handle = build_llm(config)
            
            # Should use default model since invalid-model not available
            call_args = mock_client.bind.call_args
            assert call_args[1]["model"] == "gpt-4o-mini"