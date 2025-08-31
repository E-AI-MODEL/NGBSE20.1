from __future__ import annotations

import datetime
import json
from typing import Any

from stix2 import Bundle, Indicator, Note, ThreatActor, Vulnerability, Malware, Tool

from ngbse20.logging import get_logger

LOGGER = get_logger(__name__)

HASH_LENGTH = 64

def _now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)

def _indicator_for_finding(f: dict[str, Any]) -> Indicator:
    """Create STIX indicator for a finding based on its type."""
    source_type = f.get("source", {}).get("type", "web")
    
    if source_type == "data_breach":
        # LeakIX findings
        pattern = f"[domain-name:value = '{f.get('asset', '')}']"
        name = f"Data Breach: {f.get('raw', {}).get('title', 'Unknown')}"
        
    elif source_type == "infrastructure":
        # Shodan findings
        ip = f.get("raw", {}).get("ip", "")
        port = f.get("raw", {}).get("port", "")
        pattern = f"[ipv4-addr:value = '{ip}' AND network-traffic:dst_port = {port}]"
        name = f"Infrastructure: {f.get('raw', {}).get('product', 'Unknown')} on {ip}:{port}"
        
    elif source_type == "network_intelligence":
        # Censys findings
        ip = f.get("raw", {}).get("ip", "")
        pattern = f"[ipv4-addr:value = '{ip}']"
        name = f"Network: {ip}"
        
    elif source_type == "threat_intelligence":
        # URLScan findings
        url = f.get("raw", {}).get("url", "")
        pattern = f"[url:value = '{url}']"
        name = f"Threat: {f.get('raw', {}).get('title', 'Unknown')}"
        
    elif source_type in ["code_repository", "code_search"]:
        # GitHub findings
        repo = f.get("asset", "")
        pattern = f"[url:value = '{f.get('source', {}).get('url', '')}']"
        name = f"Code: {repo}"
        
    elif source_type == "news":
        # News findings
        title = f.get("raw", {}).get("title", "")
        pattern = f"[url:value = '{f.get('source', {}).get('url', '')}']"
        name = f"News: {title[:50]}..."
        
    else:
        # Default web findings
        url = f.get("source", {}).get("url", "")
        domain = f.get("asset", "")
        pattern = f"[url:value = '{url}']" if url else f"[domain-name:value = '{domain}']"
        name = f"Web: {f.get('raw', {}).get('title', 'Unknown')}"
    
    # Truncate name to STIX limit
    name = name[:128]
    
    return Indicator(
        name=name,
        pattern=pattern,
        pattern_type="stix",
        valid_from=_now(),
        custom_properties={
            "x_ngbse20_source_type": source_type,
            "x_ngbse20_asset": f.get("asset", ""),
            "x_ngbse20_hash": f.get("hash", ""),
            "x_ngbse20_quality": f.get("quality", {}).get("q", 0.0),
            "x_ngbse20_score": f.get("score", 0.0),
        },
    )

def _create_threat_actor(f: dict[str, Any]) -> ThreatActor | None:
    """Create STIX threat actor if threat indicators are present."""
    if f.get("source", {}).get("type") == "threat_intelligence":
        threat_indicators = f.get("raw", {}).get("threat_indicators", [])
        if threat_indicators:
            return ThreatActor(
                name=f"Threat Actor - {f.get('asset', 'Unknown')}",
                threat_level="medium",
                custom_properties={
                    "x_ngbse20_threat_indicators": threat_indicators,
                    "x_ngbse20_malicious_score": f.get("raw", {}).get("malicious_score", 0),
                }
            )
    return None

def _create_vulnerability(f: dict[str, Any]) -> Vulnerability | None:
    """Create STIX vulnerability if vulnerability indicators are present."""
    if f.get("source", {}).get("type") == "infrastructure":
        product = f.get("raw", {}).get("product", "")
        version = f.get("raw", {}).get("version", "")
        if product and version:
            return Vulnerability(
                name=f"Vulnerability - {product} {version}",
                description=f"Potential vulnerability in {product} version {version}",
                custom_properties={
                    "x_ngbse20_product": product,
                    "x_ngbse20_version": version,
                    "x_ngbse20_ip": f.get("raw", {}).get("ip", ""),
                }
            )
    return None

def to_stix_bundle(findings: list[dict[str, Any]]) -> Bundle:
    """Create comprehensive STIX bundle from findings."""
    objects = []
    
    for f in findings:
        # Create indicator
        indicator = _indicator_for_finding(f)
        objects.append(indicator)
        
        # Create note with additional context
        note_content = f"""Source: {f.get('source', {}).get('url', 'N/A')}
Asset: {f.get('asset', 'N/A')}
Type: {f.get('source', {}).get('type', 'N/A')}
Timestamp: {f.get('timestamp', 'N/A')}
Quality: {f.get('quality', {}).get('q', 0.0)}
Score: {f.get('score', 0.0)}"""
        
        if f.get("raw", {}).get("description"):
            note_content += f"\nDescription: {f.get('raw', {}).get('description', '')}"
        
        note = Note(
            content=note_content,
            object_refs=[indicator],
        )
        objects.append(note)
        
        # Create additional STIX objects based on finding type
        threat_actor = _create_threat_actor(f)
        if threat_actor:
            objects.append(threat_actor)
            # Link threat actor to indicator
            note.object_refs.append(threat_actor)
        
        vulnerability = _create_vulnerability(f)
        if vulnerability:
            objects.append(vulnerability)
            # Link vulnerability to indicator
            note.object_refs.append(vulnerability)
    
    bundle = Bundle(objects=objects, allow_custom=True)
    LOGGER.info("Built STIX bundle with %d objects", len(objects))
    return bundle

def write_stix(findings: list[dict[str, Any]], path: str) -> str:
    """Write STIX bundle to file."""
    bundle = to_stix_bundle(findings)
    with open(path, "w", encoding="utf-8") as f:
        f.write(bundle.serialize(pretty=True))
    return path

def findings_to_stix(findings: list[dict[str, Any]], score_lookup=None) -> dict[str, Any]:
    """Return STIX bundle as Python dict for given findings."""
    bundle = to_stix_bundle(findings)
    return json.loads(bundle.serialize())
