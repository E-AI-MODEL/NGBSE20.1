from __future__ import annotations
from typing import List, Dict, Any
from datetime import datetime, timezone

from stix2 import Bundle, Indicator, ObservedData, Note

from ngbse20.logging import get_logger
import json

LOGGER = get_logger(__name__)

def _now():
    return datetime.now(timezone.utc)

def _indicator_for_finding(f: Dict[str, Any]) -> Indicator:
    url = f.get("url") or ""
    domain = f.get("domain") or ""
    h = f.get("hash") or ""
    # Primair: url pattern; fallback: domain
    if url:
        pattern = f"[url:value = '{url}']"
    else:
        pattern = f"[domain-name:value = '{domain}']"
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

def _observed_for_finding(f: Dict[str, Any]) -> ObservedData:
    # ObservedData met minimaal url/domain + hash als custom
    objs = {
        "0": {
            "type": "x-oca-asset",  # neutraal custom-ish object type
            "x_url": f.get("url"),
            "x_domain": f.get("domain"),
            "x_hash": f.get("hash"),
            "x_title": f.get("title"),
            "x_excerpt": f.get("excerpt", "")[:2048],
        }
    }
    return ObservedData(
        first_observed=_now(), last_observed=_now(),
        number_observed=1, object_refs=["0"], objects=objs,
    )

def to_stix_bundle(findings: List[Dict[str, Any]]) -> Bundle:
    objects = []
    for f in findings:
        ind = _indicator_for_finding(f)
        obs = _observed_for_finding(f)
        note = Note(
            content=f"Source: {f.get('url')}\nFetched: {f.get('fetched_at')}\nPublished: {f.get('published')}",
            object_refs=[ind, obs],
        )
        objects.extend([ind, obs, note])
    bundle = Bundle(objects=objects, allow_custom=True)
    LOGGER.info("Built STIX bundle with %d objects", len(objects))
    return bundle

def write_stix(findings: List[Dict[str, Any]], path: str) -> str:
    bundle = to_stix_bundle(findings)
    with open(path, "w", encoding="utf-8") as f:
        f.write(bundle.serialize(pretty=True))
    return path


def findings_to_stix(findings: List[Dict[str, Any]], score_lookup=None) -> Dict[str, Any]:
    """Return STIX bundle as Python dict for given findings."""
    bundle = to_stix_bundle(findings)
    return json.loads(bundle.serialize())
