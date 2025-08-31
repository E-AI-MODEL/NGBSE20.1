"""GitHub collector for code repository intelligence."""

import os
import requests
from typing import List, Dict, Any
from .base import BaseCollector
from ..utils.hash import content_hash


class GitHubCollector(BaseCollector):
    """Collector for GitHub code repository intelligence."""
    
    API_BASE = "https://api.github.com"
    
    def __init__(self, config: Dict[str, Any], allowlist_domains: List[str]):
        super().__init__(config, allowlist_domains)
        self.token = os.getenv("GITHUB_TOKEN")
        if not self.token:
            print("WARN: GitHub collector requires GITHUB_TOKEN env var.")
    
    def collect(self, seed: Dict[str, Any], now_iso: str) -> List[Dict[str, Any]]:
        """Collect code repository intelligence from GitHub."""
        query = seed.get("query", "")
        if "github" not in (seed.get("type", "").lower() or query.lower()):
            return []
        
        if not self.token:
            return []
        
        try:
            headers = {
                "Accept": "application/vnd.github.v3+json",
                "Authorization": f"token {self.token}"
            }
            
            # Search repositories
            repo_params = {"q": query, "sort": "updated", "order": "desc", "per_page": 50}
            repo_response = requests.get(
                f"{self.API_BASE}/search/repositories",
                headers=headers,
                params=repo_params,
                timeout=30
            )
            repo_response.raise_for_status()
            repo_data = repo_response.json()
            
            # Search code
            code_params = {"q": query, "sort": "indexed", "order": "desc", "per_page": 50}
            code_response = requests.get(
                f"{self.API_BASE}/search/code",
                headers=headers,
                params=code_params,
                timeout=30
            )
            code_response.raise_for_status()
            code_data = code_response.json()
            
        except Exception as e:
            print(f"ERROR: GitHub collector failed for query '{query}': {e}")
            return []
        
        findings = []
        
        # Process repository findings
        for repo in repo_data.get("items", []):
            repo_name = repo.get("full_name", "")
            if not self._is_allowed(f"github.com/{repo_name}"):
                continue
            
            findings.append({
                "id": f"github-repo-{repo.get('id', 'unknown')}",
                "hash": content_hash(f"{repo_name}{repo.get('description', '')}{repo.get('language', '')}"),
                "asset": f"github.com/{repo_name}",
                "raw": {
                    "name": repo_name,
                    "description": repo.get("description", ""),
                    "language": repo.get("language", ""),
                    "stars": repo.get("stargazers_count", 0),
                    "forks": repo.get("forks_count", 0),
                    "topics": repo.get("topics", []),
                    "license": repo.get("license", {}).get("name", "")
                },
                "source": {
                    "type": "code_repository",
                    "url": repo.get("html_url", ""),
                    "domain": "github.com"
                },
                "timestamp": repo.get("updated_at", now_iso),
                "quality": {"q": 0.8 if repo.get("description") else 0.6}
            })
        
        # Process code findings
        for code in code_data.get("items", []):
            repo = code.get("repository", {})
            repo_name = repo.get("full_name", "")
            if not self._is_allowed(f"github.com/{repo_name}"):
                continue
            
            findings.append({
                "id": f"github-code-{code.get('sha', 'unknown')}",
                "hash": content_hash(f"{code.get('path', '')}{code.get('sha', '')}{repo_name}"),
                "asset": f"github.com/{repo_name}",
                "raw": {
                    "path": code.get("path", ""),
                    "filename": code.get("name", ""),
                    "repository": repo_name,
                    "language": code.get("language", ""),
                    "size": code.get("size", 0),
                    "score": code.get("score", 0.0)
                },
                "source": {
                    "type": "code_search",
                    "url": code.get("html_url", ""),
                    "domain": "github.com"
                },
                "timestamp": repo.get("updated_at", now_iso),
                "quality": {"q": 0.7 if code.get("language") else 0.5}
            })
        
        return findings