"""
Tests for deterministic LLM behavior.
"""

import pytest
from unittest.mock import Mock, patch

from src.ngbse20.llm_factory import build_llm
from src.ngbse20.config.models import LLMConfig, LLMParams
from src.ngbse20.utils.validation import validate_and_normalize, create_hash
from src.ngbse20.utils.prompt_hash import hash_prompt


class TestDeterminism:
    """Test deterministic behavior of LLM system."""
    
    def test_deterministic_prompt_hashing(self):
        """Test that prompt hashing is deterministic."""
        system_prompt = "You are a helpful assistant."
        user_prompt = "What is 2+2?"
        model = "gpt-4o-mini"
        params = {"temperature": 0.0, "top_p": 1.0, "max_tokens": 100}
        seed = 42
        
        # Generate hash multiple times
        hash1 = hash_prompt(system_prompt, user_prompt, model, params, seed)
        hash2 = hash_prompt(system_prompt, user_prompt, model, params, seed)
        hash3 = hash_prompt(system_prompt, user_prompt, model, params, seed)
        
        # All hashes should be identical
        assert hash1 == hash2 == hash3
        assert len(hash1) == 64  # SHA256 hex length
    
    def test_deterministic_object_hashing(self):
        """Test that object hashing is deterministic."""
        obj = {
            "key1": "value1",
            "key2": [1, 2, 3],
            "key3": {"nested": "value"}
        }
        
        # Generate hash multiple times
        hash1 = create_hash(obj)
        hash2 = create_hash(obj)
        hash3 = create_hash(obj)
        
        # All hashes should be identical
        assert hash1 == hash2 == hash3
        assert len(hash1) == 64  # SHA256 hex length
    
    def test_deterministic_normalization(self):
        """Test that object normalization is deterministic."""
        obj = {
            "c": 3,
            "a": 1,
            "b": [3, 1, 2],
            "d": {"z": 2, "x": 1}
        }
        
        # Normalize multiple times
        norm1 = validate_and_normalize(obj, {"type": "object"})
        norm2 = validate_and_normalize(obj, {"type": "object"})
        norm3 = validate_and_normalize(obj, {"type": "object"})
        
        # All normalizations should be identical
        assert norm1 == norm2 == norm3
        
        # Check that keys are sorted
        assert list(norm1.keys()) == ["a", "b", "c", "d"]
        assert norm1["b"] == [1, 2, 3]  # List should be sorted
        assert list(norm1["d"].keys()) == ["x", "z"]  # Nested keys sorted
    
    def test_deterministic_llm_config(self):
        """Test that LLM configuration produces deterministic results."""
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
            
            # Build LLM multiple times
            handle1 = build_llm(config)
            handle2 = build_llm(config)
            handle3 = build_llm(config)
            
            # All handles should be identical (same mock object)
            assert handle1 == handle2 == handle3
            
            # Verify bind was called with same parameters each time
            assert mock_client.bind.call_count == 3
            for call in mock_client.bind.call_args_list:
                args, kwargs = call
                assert kwargs["model"] == "gpt-4o-mini"
                assert kwargs["temperature"] == 0.0
                assert kwargs["top_p"] == 1.0
                assert kwargs["max_tokens"] == 400
    
    def test_deterministic_with_seed(self):
        """Test that seed parameter is properly passed through."""
        config = LLMConfig(
            provider="openai",
            model="gpt-4o-mini",
            params=LLMParams(temperature=0.0, top_p=1.0, max_tokens=400),
            seed=12345
        )
        
        with patch('src.ngbse20.llm_factory.get_provider_client') as mock_get_client:
            mock_client = Mock()
            mock_handle = Mock()
            mock_client.list_models.return_value = ["gpt-4o-mini"]
            mock_client.default_model.return_value = "gpt-4o-mini"
            mock_client.bind.return_value = mock_handle
            mock_get_client.return_value = mock_client
            
            handle = build_llm(config)
            
            # Verify seed was passed to bind
            call_args = mock_client.bind.call_args
            assert call_args[1]["seed"] == 12345
    
    def test_deterministic_profile_application(self):
        """Test that profile application is deterministic."""
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
            
            # Apply profile multiple times
            handle1 = build_llm(config, profile)
            handle2 = build_llm(config, profile)
            handle3 = build_llm(config, profile)
            
            # All handles should be identical
            assert handle1 == handle2 == handle3
            
            # Verify profile was applied consistently
            for call in mock_client.bind.call_args_list:
                args, kwargs = call
                assert kwargs["temperature"] == 0.7  # From profile
                assert kwargs["max_tokens"] == 600   # From profile
                assert kwargs["top_p"] == 1.0        # From original config