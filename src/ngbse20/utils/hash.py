from __future__ import annotations
import hashlib
import re
from typing import Optional

_WS_RE = re.compile(r"\s+")

def normalize_text(text: str) -> str:
    """Minimal, deterministic normalisatie voor hashing."""
    return _WS_RE.sub(" ", (text or "").strip())

def sha256_hex(data: str | bytes) -> str:
    if isinstance(data, str):
        data = data.encode("utf-8", errors="ignore")
    return hashlib.sha256(data).hexdigest()

def content_hash(text: str, *, url: Optional[str] = None, title: Optional[str] = None) -> str:
    """
    Maak een stabiele hash over genormaliseerde inhoud + optionele context.
    """
    norm = normalize_text(text)
    ctx = "||".join(x for x in [title or "", url or ""] if x)
    return sha256_hex(norm + ("||" + ctx if ctx else ""))
