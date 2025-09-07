from __future__ import annotations

import json
import os
import time
from json import JSONDecodeError
from typing import Any

import requests

from .logging import get_logger

LOGGER = get_logger(__name__)

try:
    from requests.exceptions import RequestException
except Exception:  # pragma: no cover - fallback for stubbed requests

    class RequestException(Exception):
        pass


class LLMClient:
    def __init__(self, provider_priority: list[str] | None = None, config: dict[str, Any] | None = None):
        self.providers = provider_priority
        self.config = config or {}
        self._determine_provider_priority()

    def _determine_provider_priority(self) -> None:
        """Determine provider priority based on available API keys and configuration."""
        if self.providers is not None:
            # Use explicitly provided priority
            return

        # Check which API keys are available
        available_providers = []

        # Check for OpenAI
        if os.getenv("OPENAI_API_KEY"):
            available_providers.append("openai")

        # Check for Azure OpenAI
        if os.getenv("AZURE_OPENAI_API_KEY") and os.getenv("AZURE_OPENAI_ENDPOINT"):
            available_providers.append("azure_openai")

        # Check for Anthropic
        if os.getenv("ANTHROPIC_API_KEY"):
            available_providers.append("anthropic")

        # Check for Cohere
        if os.getenv("COHERE_API_KEY"):
            available_providers.append("cohere")

        # Check for Google
        if os.getenv("GOOGLE_API_KEY"):
            available_providers.append("google")

        # If no providers available, use default priority
        if not available_providers:
            self.providers = ["openai", "azure_openai", "anthropic", "cohere", "google"]
            LOGGER.warning("No API keys found, using default provider priority")
        else:
            self.providers = available_providers
            LOGGER.info(f"Using available providers: {', '.join(available_providers)}")

    def _get_model_for_provider(self, provider: str) -> str:
        """Get the appropriate model for a given provider based on configuration."""
        # Check if there's a specific model preference in config
        ballm_config = self.config.get("ballm", {})
        preferred_model = ballm_config.get("model", "")

        # Model mapping based on preferred model
        if preferred_model:
            model_mapping = {
                "gpt-4": {
                    "openai": "gpt-4",
                    "azure_openai": "gpt-4",
                    "anthropic": "claude-3-5-sonnet-20240620",
                    "cohere": "command-r7b-12-2024",
                    "google": "gemini-1.5-pro",
                },
                "gpt-4o": {
                    "openai": "gpt-4o",
                    "azure_openai": "gpt-4o",
                    "anthropic": "claude-3-5-sonnet-20240620",
                    "cohere": "command-r7b-12-2024",
                    "google": "gemini-1.5-pro",
                },
                "gpt-4o-mini": {
                    "openai": "gpt-4o-mini",
                    "azure_openai": "gpt-4o-mini",
                    "anthropic": "claude-3-5-haiku-20240307",
                    "cohere": "command-r7b-12-2024",
                    "google": "gemini-1.5-flash",
                },
                "claude": {
                    "openai": "gpt-4o-mini",
                    "azure_openai": "gpt-4o-mini",
                    "anthropic": "claude-3-5-sonnet-20240620",
                    "cohere": "command-r7b-12-2024",
                    "google": "gemini-1.5-pro",
                },
                "gemini": {
                    "openai": "gpt-4o-mini",
                    "azure_openai": "gpt-4o-mini",
                    "anthropic": "claude-3-5-haiku-20240307",
                    "cohere": "command-r7b-12-2024",
                    "google": "gemini-1.5-pro",
                },
            }

            # Find the best match for the preferred model (exact match first, then partial)
            exact_matches = []
            partial_matches = []

            for model_key, provider_models in model_mapping.items():
                if model_key == preferred_model.lower():
                    exact_matches.append((model_key, provider_models))
                elif model_key in preferred_model.lower():
                    partial_matches.append((model_key, provider_models))

            # Try exact matches first
            for _model_key, provider_models in exact_matches:
                if provider in provider_models:
                    return provider_models[provider]

            # Then try partial matches
            for _model_key, provider_models in partial_matches:
                if provider in provider_models:
                    return provider_models[provider]

        # Fallback to environment variables or defaults
        env_model_mapping = {
            "openai": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            "azure_openai": os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini"),
            "anthropic": os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20240620"),
            "cohere": os.getenv("COHERE_MODEL", "command-r7b-12-2024"),
            "google": os.getenv("GOOGLE_MODEL", "gemini-1.5-pro"),
        }

        return env_model_mapping.get(provider, "gpt-4o-mini")

    def call(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 800,
        temperature: float = 0.2,
    ) -> str | None:
        for p in self.providers or [
            "openai",
            "azure_openai",
            "anthropic",
            "cohere",
            "google",
        ]:
            fn = getattr(self, f"_call_{p}", None)
            if fn:
                LOGGER.info(f"Attempting to call LLM provider: {p}")
                out = fn(system_prompt, user_prompt, max_tokens, temperature)
                if out:
                    LOGGER.info(f"LLM call to {p} successful.")
                    return out
                else:
                    LOGGER.warning(f"LLM call to {p} failed.")
        # Universal safe fallback to avoid crashes and provide consistent structure
        LOGGER.warning("All configured LLM providers failed or are unavailable. Returning safe fallback output.")
        return json.dumps(
            {
                "BLUF": "No model output available. Using safe fallback.",
                "TopRisks": [],
                "Actions": [],
            }
        )

    def _post_json(
        self,
        url: str,
        headers: dict[str, str],
        payload: dict[str, Any],
        timeout: int = 60,
        retries: int = 2,
    ) -> dict[str, Any] | None:
        for attempt in range(retries + 1):
            try:
                r = requests.post(url, headers=headers, data=json.dumps(payload), timeout=timeout)
                r.raise_for_status()
                return r.json()
            except RequestException as e:
                LOGGER.warning(f"llm_request_error, url={url}, attempt={attempt + 1}, err={e!s}")
                if attempt == retries:
                    return None
                time.sleep(2**attempt)
            except JSONDecodeError as e:
                LOGGER.warning(f"llm_json_error, url={url}, err={e!s}")
                return None

    def _call_openai(self, system_prompt: str, user_prompt: str, max_tokens: int, temperature: float) -> str | None:
        api_key = os.getenv("OPENAI_API_KEY")
        model = self._get_model_for_provider("openai")
        if not api_key:
            return None
        data = self._post_json(
            "https://api.openai.com/v1/chat/completions",
            {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "max_tokens": max_tokens,
                "temperature": temperature,
            },
        )
        return data["choices"][0]["message"]["content"] if data and data.get("choices") else None

    def _call_azure_openai(
        self, system_prompt: str, user_prompt: str, max_tokens: int, temperature: float
    ) -> str | None:
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        deployment = self._get_model_for_provider("azure_openai")
        if not api_key or not endpoint:
            return None
        url = f"{endpoint}/openai/deployments/{deployment}/chat/completions" f"?api-version=2024-02-15-preview"
        data = self._post_json(
            url,
            {"api-key": api_key, "Content-Type": "application/json"},
            {
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "max_tokens": max_tokens,
                "temperature": temperature,
            },
        )
        return data["choices"][0]["message"]["content"] if data and data.get("choices") else None

    def _call_anthropic(self, system_prompt: str, user_prompt: str, max_tokens: int, temperature: float) -> str | None:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        model = self._get_model_for_provider("anthropic")
        if not api_key:
            return None
        data = self._post_json(
            "https://api.anthropic.com/v1/messages",
            {
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            {
                "model": model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "system": system_prompt,
                "messages": [{"role": "user", "content": user_prompt}],
            },
        )
        parts = data.get("content", []) if data else []
        return "\n".join([p.get("text", "") for p in parts if p.get("type") == "text"]) if parts else None

    def _call_cohere(self, system_prompt: str, user_prompt: str, max_tokens: int, temperature: float) -> str | None:
        """Cohere fallback implementation.

        Returns a structured fallback when COHERE_API_KEY is not configured or
        if the API call is not implemented in this environment.
        """
        api_key = os.getenv("COHERE_API_KEY")
        self._get_model_for_provider("cohere")
        if not api_key:
            # No key provided; return a consistent, safe fallback structure
            LOGGER.warning("Cohere API key not set. Using fallback response.")
            return json.dumps(
                {
                    "BLUF": "No output available (Cohere provider not configured).",
                    "TopRisks": [],
                    "Actions": [],
                }
            )
        # If in the future we implement real Cohere calls, use a pattern similar to _post_json
        LOGGER.warning("Cohere provider call not implemented. Using fallback response.")
        return json.dumps(
            {
                "BLUF": "No output available (Cohere provider not implemented).",
                "TopRisks": [],
                "Actions": [],
            }
        )

    def _call_google(self, system_prompt: str, user_prompt: str, max_tokens: int, temperature: float) -> str | None:
        api_key = os.getenv("GOOGLE_API_KEY")
        model = self._get_model_for_provider("google")
        if not api_key:
            return None
        url = "https://generativelanguage.googleapis.com/v1beta/models/" f"{model}:generateContent?key={api_key}"
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": f"System:\n{system_prompt}\n\nUser:\n{user_prompt}"}],
                }
            ],
            "generationConfig": {
                "temperature": float(temperature),
                "maxOutputTokens": int(max_tokens),
            },
        }
        data = self._post_json(url, {"Content-Type": "application/json"}, payload)
        parts = ((data.get("candidates", [{}])[0] or {}).get("content", {}) or {}).get("parts", []) if data else []
        return "\n".join([p.get("text", "") for p in parts if isinstance(p, dict)]).strip() or None
