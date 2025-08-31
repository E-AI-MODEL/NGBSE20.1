from __future__ import annotations
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
import tldextract

_UTM_PREFIXES = ("utm_", "icid", "gclid", "fbclid", "mc_cid", "mc_eid")

def normalize_url(raw: str) -> str:
    """
    Canonicaliseer URL: lowercase host, fragment weg, sorteer query, drop tracking params.
    """
    parts = urlsplit(raw)
    scheme = parts.scheme or "http"
    netloc = parts.netloc.lower()
    # strip default ports
    if netloc.endswith(":80") and scheme == "http":
        netloc = netloc[:-3]
    elif netloc.endswith(":443") and scheme == "https":
        netloc = netloc[:-4]
    path = parts.path or "/"
    query_pairs = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True)
                   if not k.lower().startswith(_UTM_PREFIXES)]
    query_pairs.sort()
    query = urlencode(query_pairs, doseq=True)
    return urlunsplit((scheme, netloc, path, query, ""))

def extract_domain(raw: str) -> str:
    ext = tldextract.extract(raw)
    if not ext.registered_domain:
        return (ext.fqdn or raw).lower()
    return ext.registered_domain.lower()
