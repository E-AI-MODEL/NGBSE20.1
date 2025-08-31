from __future__ import annotations

import requests
from bs4 import BeautifulSoup

from ngbse20.utils.hash import content_hash
from ngbse20.utils.url import normalize_url

HTTP_ERROR_THRESHOLD = 400


def fetch(url: str):
    url_norm = normalize_url(url)
    try:
        resp = requests.get(url_norm, timeout=15)
        if resp.status_code >= HTTP_ERROR_THRESHOLD:
            return None
        ctype = resp.headers.get("Content-Type", "")
        if "text/html" not in ctype and "application/xhtml+xml" not in ctype:
            return None
        text = resp.text
    except Exception:
        return None
    soup = BeautifulSoup(text, "html.parser")
    title = (soup.title.string if soup.title else "") or ""
    content = soup.get_text(separator=" ", strip=True)
    h = content_hash(content, url=url_norm, title=title)
    return {"url": url_norm, "title": title.strip(), "content_hash": h}
