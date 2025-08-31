from __future__ import annotations

import asyncio
import datetime
import time
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from typing import Any
from urllib import robotparser
from urllib.parse import urlsplit, urlunsplit

import aiohttp
from bs4 import BeautifulSoup

from ngbse20.logging import get_logger
from ngbse20.utils.hash import content_hash
from ngbse20.utils.url import extract_domain, normalize_url

LOGGER = get_logger(__name__)

DEFAULT_UA = "NGBSE20.1-Collector (+https://example.invalid)"
DEFAULT_TIMEOUT = aiohttp.ClientTimeout(total=20, connect=7, sock_read=15)
MAX_CONCURRENCY = 10
PER_DOMAIN_DELAY_SEC = 1.0
HTTP_ERROR_THRESHOLD = 400
EXCERPT_LIMIT = 500

@dataclass
class Finding:
    id: str
    type: str
    url: str
    domain: str
    title: str
    published: str | None
    fetched_at: str
    excerpt: str
    hash: str
    meta: dict[str, Any]

def _now_iso() -> str:
    return datetime.datetime.now(datetime.UTC).isoformat()

async def _fetch(session: aiohttp.ClientSession, url: str) -> str | None:
    try:
        async with session.get(url) as resp:
            if resp.status >= HTTP_ERROR_THRESHOLD:
                LOGGER.warning("HTTP %s for %s", resp.status, url)
                return None
            ctype = resp.headers.get("Content-Type", "")
            if "text/html" not in ctype and "application/xhtml+xml" not in ctype:
                LOGGER.debug("Skip non-HTML %s (%s)", url, ctype)
                return None
            return await resp.text(errors="ignore")
    except Exception as e:
        LOGGER.warning("Fetch error for %s: %s", url, e)
        return None

def _robots_allows(url: str, user_agent: str) -> bool:
    # Robots per host
    try:
        base = normalize_url(url)
        rp = robotparser.RobotFileParser()
        # Build robots.txt URL
        parts = urlsplit(base)
        robots_url = urlunsplit((parts.scheme, parts.netloc, "/robots.txt", "", ""))
        rp.set_url(robots_url)
        # Small timeout via read()
        rp.read()
        return rp.can_fetch(user_agent, base)
    except Exception:
        return True  # fail open to avoid hard stops in demo contexts

def _parse_html(url: str, html: str, fetched_at: str) -> Finding:
    soup = BeautifulSoup(html, "html.parser")
    title = (soup.title.string if soup.title else "") or ""
    title = title.strip()
    # Try some common published-time metas
    published = None
    for key in ("article:published_time", "og:published_time", "publish-date", "date", "dc.date"):
        tag = soup.find("meta", attrs={"property": key}) or soup.find("meta", attrs={"name": key})
        if tag and tag.get("content"):
            published = tag["content"].strip()
            break
    # Build excerpt (first 500 chars of text)
    text = soup.get_text(separator=" ", strip=True)
    excerpt = (text[:EXCERPT_LIMIT] + "…") if len(text) > EXCERPT_LIMIT else text
    h = content_hash(text, url=url, title=title)
    domain = extract_domain(url)
    fid = h[:16]
    return Finding(
        id=fid,
        type="web Finding",
        url=url,
        domain=domain,
        title=title or domain,
        published=published,
        fetched_at=fetched_at,
        excerpt=excerpt,
        hash=h,
        meta={
            "length": len(text),
            "has_title": bool(title),
        },
    )

async def collect_urls(
    urls: Iterable[str],
    *,
    user_agent: str = DEFAULT_UA,
    concurrency: int = MAX_CONCURRENCY,
    per_domain_delay_sec: float = PER_DOMAIN_DELAY_SEC,
    timeout: aiohttp.ClientTimeout = DEFAULT_TIMEOUT,
) -> list[dict[str, Any]]:
    """
    Concurrent, polite collector met robots.txt-respect, per-domain pace en echte hashes.
    Returns list[dict] findings.
    """
    urls_norm = [normalize_url(u) for u in urls]
    LOGGER.info("Collecting %d urls (concurrency=%d)", len(urls_norm), concurrency)

    # Per-domain pacing
    last_request_ts: dict[str, float] = {}
    domain_locks: dict[str, asyncio.Lock] = {}

    async def _paced_fetch(session: aiohttp.ClientSession, url: str) -> dict[str, Any] | None:
        if not _robots_allows(url, user_agent):
            LOGGER.info("Robots disallow: %s", url)
            return None
        dom = extract_domain(url)
        lock = domain_locks.setdefault(dom, asyncio.Lock())
        async with lock:
            now = time.monotonic()
            last = last_request_ts.get(dom, 0.0)
            wait = per_domain_delay_sec - (now - last)
            if wait > 0:
                await asyncio.sleep(wait)
            last_request_ts[dom] = time.monotonic()
            html = await _fetch(session, url)
        if not html:
            return None
        f = _parse_html(url, html, fetched_at=_now_iso())
        return asdict(f)

    connector = aiohttp.TCPConnector(ssl=False, limit=0)
    headers = {
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
    }
    sem = asyncio.Semaphore(max(1, min(concurrency, MAX_CONCURRENCY)))
    async with aiohttp.ClientSession(
        connector=connector, headers=headers, timeout=timeout
    ) as session:
        async def _task(u: str):
            async with sem:
                return await _paced_fetch(session, u)

        tasks = [_task(u) for u in urls_norm]
        results = await asyncio.gather(*tasks, return_exceptions=False)
    findings = [r for r in results if r]
    LOGGER.info("Collected %d/%d findings", len(findings), len(urls_norm))
    return findings
