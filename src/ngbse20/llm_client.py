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
    def __init__(self, provider_priority: list[str] | None = None):
        self.providers = provider_priority

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
        return None

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
                r = requests.post(
                    url, headers=headers, data=json.dumps(payload), timeout=timeout
                )
                r.raise_for_status()
                return r.json()
            except RequestException as e:
                LOGGER.warning(
                    f"llm_request_error, url={url}, attempt={attempt + 1}, err={e!s}"
                )
                if attempt == retries:
                    return None
                time.sleep(2**attempt)
            except JSONDecodeError as e:
                LOGGER.warning(f"llm_json_error, url={url}, err={e!s}")
                return None

    def _call_openai(
        self, system_prompt: str, user_prompt: str, max_tokens: int, temperature: float
    ) -> str | None:
        api_key = os.getenv("OPENAI_API_KEY")
        model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
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
        return (
            data["choices"][0]["message"]["content"]
            if data and data.get("choices")
            else None
        )

    def _call_azure_openai(
        self, system_prompt: str, user_prompt: str, max_tokens: int, temperature: float
    ) -> str | None:
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")
        if not api_key or not endpoint:
            return None
        url = f"{endpoint}/openai/deployments/{deployment}/chat/completions?api-version=2024-02-15-preview"
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
        return (
            data["choices"][0]["message"]["content"]
            if data and data.get("choices")
            else None
        )

    def _call_anthropic(
        self, system_prompt: str, user_prompt: str, max_tokens: int, temperature: float
    ) -> str | None:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        model = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20240620")
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
        return (
            "\n".join([p.get("text", "") for p in parts if p.get("type") == "text"])
            if parts
            else None
        )

    def _call_google(
        self, system_prompt: str, user_prompt: str, max_tokens: int, temperature: float
    ) -> str | None:
        api_key = os.getenv("GOOGLE_API_KEY")
        model = os.getenv("GOOGLE_MODEL", "gemini-1.5-pro")
        if not api_key:
            return None
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{model}:generateContent?key={api_key}"
        )
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {"text": f"System:\n{system_prompt}\n\nUser:\n{user_prompt}"}
                    ],
                }
            ],
            "generationConfig": {
                "temperature": float(temperature),
                "maxOutputTokens": int(max_tokens),
            },
        }
        data = self._post_json(url, {"Content-Type": "application/json"}, payload)
        parts = (
            ((data.get("candidates", [{}])[0] or {}).get("content", {}) or {}).get(
                "parts", []
            )
            if data
            else []
        )
        return (
            "\n".join([p.get("text", "") for p in parts if isinstance(p, dict)]).strip()
            or None
        )
