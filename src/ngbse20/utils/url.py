from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import tldextract

_UTM_PREFIXES = ("utm_", "icid", "gclid", "fbclid", "mc_cid", "mc_eid")


def normalize_url(raw: str) -> str:
    """
    Canonicalize URL: lowercase host, remove fragment, sort query, drop tracking params.
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
    query_pairs = [
        (k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True) if not k.lower().startswith(_UTM_PREFIXES)
    ]
    query_pairs.sort()
    query = urlencode(query_pairs, doseq=True)
    return urlunsplit((scheme, netloc, path, query, ""))


def extract_domain(raw: str) -> str:
    ext = tldextract.extract(raw)
    # Use top_domain_under_public_suffix instead of deprecated registered_domain
    if not ext.top_domain_under_public_suffix:
        return (ext.fqdn or raw).lower()
    return ext.top_domain_under_public_suffix.lower()
