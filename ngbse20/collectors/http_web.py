import re
import urllib.parse
from typing import List, Dict, Any

try:
    import requests
except Exception:  # simple fallback using urllib
    import urllib.request as requests

META_DATE_RE = re.compile(r"(20\d{2}-\d{2}-\d{2})")
TITLE_RE = re.compile(r"<title>(.*?)</title>", re.IGNORECASE | re.DOTALL)


def parse_published(html: str) -> str:
    m = META_DATE_RE.search(html)
    return m.group(1) if m else ""


def extract_domain(url: str) -> str:
    host = urllib.parse.urlparse(url).netloc.split('@')[-1].split(':')[0]
    if host.startswith("www."):
        host = host[4:]
    return host


class HttpWebCollector:
    def __init__(self, allowlist_domains: List[str]):
        self.allow_domains = [d.lower() for d in allowlist_domains]

    def _is_allowed(self, domain: str) -> bool:
        d = (domain or "").lower()
        if not self.allow_domains or "*" in self.allow_domains:
            return True
        if d in self.allow_domains:
            return True
        for entry in self.allow_domains:
            if entry.startswith('.') and d.endswith(entry):
                return True
        return False

    def collect(self, seed: Dict[str, Any], now_iso: str) -> List[Dict[str, Any]]:
        query = seed.get("query", "")
        urls = re.findall(r"https?://[^\s\"'>]+", query)
        findings = []
        for url in urls:
            domain = extract_domain(url)
            if not self._is_allowed(domain):
                print(f"WARN: Domain not in allowlist, skipping: {domain}")
                continue
            try:
                r = requests.get(url) if hasattr(requests, 'get') else requests.urlopen(url)
                text = r.text if hasattr(r, 'text') else r.read().decode('utf-8', 'ignore')
                text = text[:500000]
                published = parse_published(text)
                mt = TITLE_RE.search(text)
                title = mt.group(1).strip() if mt else ""
                status = getattr(r, 'status_code', getattr(r, 'status', 200))
                findings.append({
                    "id": f"finding-{seed.get('id', 'unknown')}-{len(findings)}",
                    "hash": "hash-placeholder",
                    "asset": domain.lower(),
                    "raw": {"url": url, "status": status, "title": title},
                    "source": {"type": seed.get("type","web"), "url": url, "domain": domain},
                    "timestamp": published or now_iso,
                    "quality": {"q": 0.6 if status==200 else 0.3}
                })
            except Exception as e:
                print(f"ERROR: Collector failed for {url}: {e}")
        return findings
