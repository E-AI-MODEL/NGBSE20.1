"""GitHub collector for code repository intelligence."""

import os
from typing import Any

import requests

from ..logging import get_logger
from ..utils.hash import content_hash
from ..utils.rate_limiter import api_rate_limited, retry_with_backoff
from ..utils.security import mask_api_key, sanitize_error_message
from .base import BaseCollector

LOGGER = get_logger(__name__)


class GitHubCollector(BaseCollector):
    """Collector for GitHub code repository intelligence."""

    API_BASE = "https://api.github.com"

    def __init__(self, config: dict[str, Any], allowlist_domains: list[str]):
        super().__init__(config, allowlist_domains)
        self.token = os.getenv("GITHUB_TOKEN")
        if not self.token:
            LOGGER.warning("GitHub collector requires GITHUB_TOKEN env var.")
        else:
            LOGGER.debug(f"GitHub collector initialized with token: {mask_api_key(self.token)}")

    def collect(self, seed: dict[str, Any], now_iso: str) -> list[dict[str, Any]]:
        """Collect code repository intelligence from GitHub."""
        query = seed.get("query", "")
        if "github" not in (seed.get("type", "").lower() or query.lower()):
            return []

        if not self.token:
            return []

        try:
            repo_response, code_response = self._make_api_requests(query)
            repo_data = repo_response.json()
            code_data = code_response.json()

        except Exception as e:
            sanitized_error = sanitize_error_message(str(e), {"token": self.token})
            LOGGER.error(f"GitHub collector failed for query '{query}': {sanitized_error}")
            return []

        findings = []

        # Process repository findings
        for repo in repo_data.get("items", []):
            repo_name = repo.get("full_name", "")
            if not self._is_allowed(f"github.com/{repo_name}"):
                continue

            findings.append(
                {
                    "id": f"github-repo-{repo.get('id', 'unknown')}",
                    "hash": content_hash(f"{repo_name}{repo.get('description', '')}" f"{repo.get('language', '')}"),
                    "asset": f"github.com/{repo_name}",
                    "raw": {
                        "name": repo_name,
                        "description": repo.get("description", ""),
                        "language": repo.get("language", ""),
                        "stars": repo.get("stargazers_count", 0),
                        "forks": repo.get("forks_count", 0),
                        "topics": repo.get("topics", []),
                        "license": repo.get("license", {}).get("name", ""),
                    },
                    "source": {
                        "type": "code_repository",
                        "url": repo.get("html_url", ""),
                        "domain": "github.com",
                    },
                    "timestamp": repo.get("updated_at", now_iso),
                    "quality": {"q": 0.8 if repo.get("description") else 0.6},
                }
            )

        # Process code findings
        for code in code_data.get("items", []):
            repo = code.get("repository", {})
            repo_name = repo.get("full_name", "")
            if not self._is_allowed(f"github.com/{repo_name}"):
                continue

            findings.append(
                {
                    "id": f"github-code-{code.get('sha', 'unknown')}",
                    "hash": content_hash(f"{code.get('path', '')}{code.get('sha', '')}{repo_name}"),
                    "asset": f"github.com/{repo_name}",
                    "raw": {
                        "path": code.get("path", ""),
                        "filename": code.get("name", ""),
                        "repository": repo_name,
                        "language": code.get("language", ""),
                        "size": code.get("size", 0),
                        "score": code.get("score", 0.0),
                    },
                    "source": {
                        "type": "code_search",
                        "url": code.get("html_url", ""),
                        "domain": "github.com",
                    },
                    "timestamp": repo.get("updated_at", now_iso),
                    "quality": {"q": 0.7 if code.get("language") else 0.5},
                }
            )

        return findings

    @retry_with_backoff(max_retries=3, base_delay=1.0)
    @api_rate_limited("github")
    def _make_api_requests(self, query: str):
        """Make rate-limited API requests to GitHub."""
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"token {self.token}",
        }

        # Search repositories
        repo_params = {"q": query, "sort": "updated", "order": "desc", "per_page": 50}
        repo_response = requests.get(
            f"{self.API_BASE}/search/repositories",
            headers=headers,
            params=repo_params,
            timeout=30,
        )
        repo_response.raise_for_status()

        # Search code
        code_params = {"q": query, "sort": "indexed", "order": "desc", "per_page": 50}
        code_response = requests.get(
            f"{self.API_BASE}/search/code",
            headers=headers,
            params=code_params,
            timeout=30,
        )
        code_response.raise_for_status()

        return repo_response, code_response
