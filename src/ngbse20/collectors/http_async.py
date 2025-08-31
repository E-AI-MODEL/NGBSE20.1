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

DEFAULT_UA = "NGBSE20.1-Collector (+https://github.com/E-AI-MODEL/NGBSE20.1)"
DEFAULT_TIMEOUT = aiohttp.ClientTimeout(total=20, connect=7, sock_read=15)
MAX_CONCURRENCY = 10
PER_DOMAIN_DELAY_SEC = 1.0
HTTP_ERROR_THRESHOLD = 400
EXCERPT_LIMIT = 500
MAX_RETRIES = 3
RETRY_DELAY_BASE = 1.0

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
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

async def _fetch_with_retry(session: aiohttp.ClientSession, url: str, max_retries: int = MAX_RETRIES) -> str | None:
    """Fetch URL with exponential backoff retry logic."""
    for attempt in range(max_retries + 1):
        try:
            async with session.get(url) as resp:
                if resp.status >= HTTP_ERROR_THRESHOLD:
                    LOGGER.warning("HTTP %s for %s (attempt %d/%d)", resp.status, url, attempt + 1, max_retries + 1)
                    if attempt == max_retries:
                        return None
                    await asyncio.sleep(RETRY_DELAY_BASE * (2 ** attempt))
                    continue
                
                ctype = resp.headers.get("Content-Type", "")
                if "text/html" not in ctype and "application/xhtml+xml" not in ctype:
                    LOGGER.debug("Skip non-HTML %s (%s)", url, ctype)
                    return None
                
                return await resp.text(errors="ignore")
                
        except asyncio.TimeoutError:
            LOGGER.warning("Timeout for %s (attempt %d/%d)", url, attempt + 1, max_retries + 1)
            if attempt == max_retries:
                return None
            await asyncio.sleep(RETRY_DELAY_BASE * (2 ** attempt))
        except Exception as e:
            LOGGER.warning("Fetch error for %s (attempt %d/%d): %s", url, attempt + 1, max_retries + 1, e)
            if attempt == max_retries:
                return None
            await asyncio.sleep(RETRY_DELAY_BASE * (2 ** attempt))
    
    return None

def _robots_allows(url: str, user_agent: str) -> bool:
    """Check robots.txt with better error handling."""
    try:
        base = normalize_url(url)
        rp = robotparser.RobotFileParser()
        parts = urlsplit(base)
        robots_url = urlunsplit((parts.scheme, parts.netloc, "/robots.txt", "", ""))
        rp.set_url(robots_url)
        rp.read()
        return rp.can_fetch(user_agent, base)
    except Exception as e:
        LOGGER.debug("Robots.txt check failed for %s: %s", url, e)
        # Default to allowing if robots.txt check fails
        return True

def _parse_html(url: str, html: str, fetched_at: str) -> Finding:
    """Parse HTML with enhanced error handling and content extraction."""
    try:
        soup = BeautifulSoup(html, "html.parser")
        
        # Extract title with fallbacks
        title = ""
        if soup.title and soup.title.string:
            title = soup.title.string.strip()
        elif soup.find("h1"):
            title = soup.find("h1").get_text(strip=True)
        elif soup.find("meta", attrs={"property": "og:title"}):
            title = soup.find("meta", attrs={"property": "og:title"})["content"].strip()
        
        # Extract publication date with multiple fallbacks
        published = None
        date_selectors = [
            ("meta", {"property": "article:published_time"}),
            ("meta", {"property": "og:published_time"}),
            ("meta", {"name": "publish-date"}),
            ("meta", {"name": "date"}),
            ("meta", {"name": "dc.date"}),
            ("time", {}),
            ("span", {"class": "date"}),
            ("div", {"class": "date"})
        ]
        
        for tag, attrs in date_selectors:
            element = soup.find(tag, attrs=attrs)
            if element:
                if tag == "time" and element.get("datetime"):
                    published = element["datetime"].strip()
                    break
                elif element.get("content"):
                    published = element["content"].strip()
                    break
                elif element.get_text(strip=True):
                    published = element.get_text(strip=True)
                    break
        
        # Extract text content with better cleaning
        text = soup.get_text(separator=" ", strip=True)
        # Remove excessive whitespace
        text = " ".join(text.split())
        
        excerpt = (text[:EXCERPT_LIMIT] + "…") if len(text) > EXCERPT_LIMIT else text
        h = content_hash(text, url=url, title=title)
        domain = extract_domain(url)
        fid = h[:16]
        
        # Enhanced metadata
        meta = {
            "length": len(text),
            "has_title": bool(title),
            "has_meta_description": bool(soup.find("meta", attrs={"name": "description"})),
            "has_og_tags": bool(soup.find("meta", attrs={"property": "og:"})),
            "language": soup.get("lang", ""),
            "word_count": len(text.split()),
        }
        
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
            meta=meta,
        )
    except Exception as e:
        LOGGER.error("HTML parsing failed for %s: %s", url, e)
        # Return minimal finding on parse failure
        domain = extract_domain(url)
        h = content_hash("", url=url, title="")
        return Finding(
            id=h[:16],
            type="web Finding",
            url=url,
            domain=domain,
            title=domain,
            published=None,
            fetched_at=fetched_at,
            excerpt="[Parse error]",
            hash=h,
            meta={"parse_error": str(e), "length": 0, "has_title": False},
        )

async def collect_urls(
    urls: Iterable[str],
    *,
    user_agent: str = DEFAULT_UA,
    concurrency: int = MAX_CONCURRENCY,
    per_domain_delay_sec: float = PER_DOMAIN_DELAY_SEC,
    timeout: aiohttp.ClientTimeout = DEFAULT_TIMEOUT,
    max_retries: int = MAX_RETRIES,
) -> list[dict[str, Any]]:
    """Collect URLs with enhanced error handling and performance optimizations."""
    urls_norm = [normalize_url(u) for u in urls]
    LOGGER.info("Collecting %d urls (concurrency=%d, max_retries=%d)", len(urls_norm), concurrency, max_retries)

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
            
            html = await _fetch_with_retry(session, url, max_retries)
        
        if not html:
            return None
        
        f = _parse_html(url, html, fetched_at=_now_iso())
        return asdict(f)

    # Enhanced connection pooling and session management
    connector = aiohttp.TCPConnector(
        ssl=False, 
        limit=0,  # No connection limit
        limit_per_host=concurrency,
        ttl_dns_cache=300,  # 5 minute DNS cache
        use_dns_cache=True,
    )
    
    headers = {
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }
    
    semaphore_value = max(1, min(concurrency, MAX_CONCURRENCY))
    sem = asyncio.Semaphore(semaphore_value)
    
    async with aiohttp.ClientSession(
        connector=connector, 
        headers=headers, 
        timeout=timeout,
        raise_for_status=False,
    ) as session:
        async def _task(u: str):
            async with sem:
                return await _paced_fetch(session, u)

        tasks = [_task(u) for u in urls_norm]
        results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Filter out exceptions and None results
    findings = [r for r in results if r and not isinstance(r, Exception)]
    
    # Log any exceptions that occurred
    exceptions = [r for r in results if isinstance(r, Exception)]
    if exceptions:
        LOGGER.warning("Encountered %d exceptions during collection", len(exceptions))
        for exc in exceptions[:3]:  # Log first 3 exceptions
            LOGGER.debug("Collection exception: %s", exc)
    
    LOGGER.info("Collected %d/%d findings (%.1f%% success rate)", 
                len(findings), len(urls_norm), (len(findings) / len(urls_norm)) * 100)
    
    return findings