"""LeakIX collector for data breach intelligence."""

import os
import requests
from typing import List, Dict, Any
from .base import BaseCollector
from ..utils.hash import content_hash


class LeakIXCollector(BaseCollector):
    """Collector for LeakIX data breach intelligence."""
    
    API_BASE = "https://leakix.net/api"
    
    def __init__(self, config: Dict[str, Any], allowlist_domains: List[str]):
        super().__init__(config, allowlist_domains)
        self.api_key = os.getenv("LEAKIX_API_KEY")
        if not self.api_key:
            print("WARN: LeakIX collector requires LEAKIX_API_KEY env var.")
    
    def collect(self, seed: Dict[str, Any], now_iso: str) -> List[Dict[str, Any]]:
        """Collect data breach intelligence from LeakIX."""
        query = seed.get("query", "")
        if "leakix" not in (seed.get("type", "").lower() or query.lower()):
            return []
        
        if not self.api_key:
            return []
        
        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            params = {"q": query, "size": 50}
            
            response = requests.get(
                f"{self.API_BASE}/search",
                headers=headers,
                params=params,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
        except Exception as e:
            print(f"ERROR: LeakIX collector failed for query '{query}': {e}")
            return []
        
        findings = []
        for item in data.get("results", []):
            domain = item.get("domain", "")
            if not self._is_allowed(domain):
                continue
            
            findings.append({
                "id": f"leakix-{item.get('id', 'unknown')}",
                "hash": content_hash(f"{domain}{item.get('title', '')}{item.get('content', '')}"),
                "asset": domain.lower(),
                "raw": {
                    "title": item.get("title", ""),
                    "content": item.get("content", ""),
                    "type": item.get("type", ""),
                    "severity": item.get("severity", "medium")
                },
                "source": {
                    "type": "data_breach",
                    "url": f"https://leakix.net/breach/{item.get('id', '')}",
                    "domain": domain
                },
                "timestamp": item.get("discovered_at", now_iso),
                "quality": {"q": 0.8 if item.get("verified") else 0.5}
            })
        
        return findings