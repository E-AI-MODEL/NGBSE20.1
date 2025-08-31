from __future__ import annotations
from typing import Iterable, List, Dict, Any

from ngbse20.collectors.http_async import collect_urls


class AsyncHTTPCollector:
    def __init__(self, max_concurrency: int = 10):
        self.max_concurrency = max_concurrency

    async def collect(self, urls: Iterable[str]) -> List[Dict[str, Any]]:
        findings = await collect_urls(urls, concurrency=self.max_concurrency)
        for f in findings:
            if "hash" in f and "content_hash" not in f:
                f["content_hash"] = f["hash"]
        return findings
