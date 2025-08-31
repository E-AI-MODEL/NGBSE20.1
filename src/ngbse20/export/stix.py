from __future__ import annotations

import datetime
import json
from typing import Any

from stix2 import Bundle, Indicator, Note

from ngbse20.logging import get_logger

LOGGER = get_logger(__name__)

HASH_LENGTH = 64

def _now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)

def _indicator_for_finding(f: dict[str, Any]) -> Indicator:
    url = f.get("url") or ""
    domain = f.get("domain") or ""
    h = f.get("hash") or ""
    # Primair: url pattern; fallback: domain
    pattern = f"[url:value = '{url}']" if url else f"[domain-name:value = '{domain}']"
    name = (f.get("title") or "Web Finding").strip()[:128]
    return Indicator(
        name=name,
        pattern=pattern,
        pattern_type="stix",
        valid_from=_now(),
        custom_properties={
            "x_ngbse20_domain": domain,
            "x_ngbse20_hash": h,
        },
    )

def to_stix_bundle(findings: list[dict[str, Any]]) -> Bundle:
    objects = []
    for f in findings:
        ind = _indicator_for_finding(f)
        note = Note(
            content=(
                f"Source: {f.get('url')}\n"
                f"Fetched: {f.get('fetched_at')}\n"
                f"Published: {f.get('published')}"
            ),
            object_refs=[ind],
        )
        objects.extend([ind, note])
    bundle = Bundle(objects=objects, allow_custom=True)
    LOGGER.info("Built STIX bundle with %d objects", len(objects))
    return bundle

def write_stix(findings: list[dict[str, Any]], path: str) -> str:
    bundle = to_stix_bundle(findings)
    with open(path, "w", encoding="utf-8") as f:
        f.write(bundle.serialize(pretty=True))
    return path


def findings_to_stix(findings: list[dict[str, Any]], score_lookup=None) -> dict[str, Any]:
    """Return STIX bundle as Python dict for given findings."""
    bundle = to_stix_bundle(findings)
    return json.loads(bundle.serialize())
