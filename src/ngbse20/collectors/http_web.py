import re
import urllib.parse
from typing import Any

import requests

try:
    from bs4 import BeautifulSoup
except Exception:
    BeautifulSoup = None
try:
    import tldextract
except Exception:
    tldextract = None

META_DATE_RE = re.compile(r"(20\d{2}-\d{2}-\d{2})")
TITLE_RE = re.compile(r"<title>(.*?)</title>", re.IGNORECASE | re.DOTALL)

HTTP_OK = 200


def parse_published(html: str) -> str:
    if BeautifulSoup:
        soup = BeautifulSoup(html, "html.parser")
        # try common meta tags
        for tag_name, attrs in [
            ("meta", {"property": "article:published_time"}),
            ("meta", {"name": "date"}),
            ("meta", {"itemprop": "datePublished"}),
            ("time", {}),
        ]:
            node = soup.find(tag_name, attrs=attrs)
            if node:
                content = node.get("content") or node.get_text(strip=True)
                if content and META_DATE_RE.search(content):
                    return content
    m = META_DATE_RE.search(html)
    return m.group(1) if m else ""


def extract_domain(url: str) -> str:
    if tldextract:
        ext = tldextract.extract(url)
        return ".".join(p for p in [ext.domain, ext.suffix] if p)
    host = urllib.parse.urlparse(url).netloc.split("@")[-1].split(":")[0]
    if host.startswith("www."):
        host = host[4:]
    return host


class HttpWebCollector:
    def __init__(self, allowlist_domains: list[str]):
        self.allow_domains = [d.lower() for d in allowlist_domains]

    def _is_allowed(self, domain: str) -> bool:
        d = (domain or "").lower()
        if not self.allow_domains or "*" in self.allow_domains:
            return True
        if d in self.allow_domains:
            return True
        return any(entry.startswith(".") and d.endswith(entry) for entry in self.allow_domains)

    def collect(self, seed: dict[str, Any], now_iso: str) -> list[dict[str, Any]]:
        query = seed.get("query", "")
        urls = re.findall(r"https?://[^\s\"'>]+", query)
        findings = []
        for url in urls:
            domain = extract_domain(url)
            if not self._is_allowed(domain):
                print(f"WARN: Domain not in allowlist, skipping: {domain}")
                continue
            try:
                r = requests.get(url, timeout=15)
                text = r.text
                status = r.status_code

                text = text[:500000]
                published = parse_published(text)
                title = ""
                if BeautifulSoup:
                    soup = BeautifulSoup(text, "html.parser")
                    if soup.title and soup.title.string:
                        title = soup.title.string.strip()
                else:
                    mt = TITLE_RE.search(text)
                    title = mt.group(1).strip() if mt else ""

                findings.append({
                    "id": f"finding-{seed.get('id', 'unknown')}-{len(findings)}",
                    "hash": "hash-placeholder",
                    "asset": domain.lower(),
                    "raw": {"url": url, "status": status, "title": title},
                    "source": {"type": seed.get("type","web"), "url": url, "domain": domain},
                    "timestamp": published or now_iso,
                    "quality": {"q": 0.6 if status == HTTP_OK else 0.3}
                })
            except Exception as e:
                print(f"ERROR: Collector failed for {url}: {e}")
        return findings
