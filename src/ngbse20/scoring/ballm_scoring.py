"""
BALLM (Blindspot-Aware Large Language Models) Scoring Engine v20.1

This module implements the dual-layer architecture from the research paper:
1. Answer Layer - standard scoring and analysis
2. Meta-Layer - blind spots, assumptions, and epistemic gaps

Based on "From Closure to Curiosity: Blindspot-Aware Large Language Models (BALLMs)"
by Hans Visser (August 2025)
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from ..logging import get_logger

LOGGER = get_logger(__name__)

@dataclass
class BlindspotAnalysis:
    """Represents identified blind spots and epistemic gaps."""
    type: str  # "coverage", "recency", "confidence", "assumption", "contradiction"
    severity: float  # 0.0 to 1.0
    description: str
    evidence: list[str]
    mitigation_suggestions: list[str]
    epistemic_score: float  # How much this blindspot affects overall confidence

@dataclass
class EpistemicMetaLayer:
    """Meta-layer containing blind spots and epistemic analysis."""
    blindspots: list[BlindspotAnalysis]
    assumptions: list[str]
    confidence_gaps: list[str]
    curiosity_amplification_index: float  # CAI score
    epistemic_humility_score: float
    overall_epistemic_quality: float

@dataclass
class BALLMScoringConfig:
    """Configuration for BALLM-aware scoring."""
    # Base scoring weights
    weights: dict[str, float] = field(default_factory=lambda: {
        "source": 0.25,
        "content": 0.25,
        "recency": 0.20,
        "epistemic": 0.30,  # New epistemic dimension
    })
    
    # Blindspot detection thresholds
    blindspot_thresholds: dict[str, float] = field(default_factory=lambda: {
        "coverage_gap": 0.3,
        "recency_gap": 0.4,
        "confidence_gap": 0.5,
        "assumption_risk": 0.6,
    })
    
    # Epistemic scoring parameters
    epistemic_params: dict[str, float] = field(default_factory=lambda: {
        "humility_bonus": 0.1,
        "uncertainty_penalty": 0.05,
        "contradiction_penalty": 0.15,
        "novelty_bonus": 0.08,
    })

DEFAULT_CONFIG = BALLMScoringConfig()

def _calculate_recency_score(timestamp: datetime | None, half_life_days: int = 30) -> float:
    """Calculate recency score with exponential decay."""
    if not timestamp:
        return 0.0
    
    now = datetime.now(UTC)
    age_days = max(0.0, (now - timestamp).total_seconds() / 86400.0)
    return 0.5 ** (age_days / float(half_life_days))

def _calculate_source_credibility(finding: dict[str, Any]) -> float:
    """Calculate source credibility score based on domain reputation and metadata."""
    domain = finding.get("domain", "")
    meta = finding.get("meta", {})
    
    # Domain-based credibility scoring
    credible_domains = {
        "bleepingcomputer.com": 0.95,
        "securityweek.com": 0.90,
        "darkreading.com": 0.88,
        "infosecurity-magazine.com": 0.85,
        "cyberdefensemagazine.com": 0.82,
    }
    
    base_score = credible_domains.get(domain, 0.5)
    
    # Adjust based on metadata
    if meta.get("has_title"):
        base_score += 0.05
    if meta.get("length", 0) > 100:
        base_score += 0.03
    
    return min(1.0, base_score)

def _calculate_content_quality(finding: dict[str, Any]) -> float:
    """Calculate content quality score."""
    excerpt = finding.get("excerpt", "")
    title = finding.get("title", "")
    
    if not excerpt or not title:
        return 0.0
    
    # Content length and structure scoring
    length_score = min(1.0, len(excerpt) / 500.0)
    title_score = 1.0 if len(title) > 10 else 0.5
    
    # Keyword relevance (basic implementation)
    cybersecurity_keywords = [
        "threat", "attack", "vulnerability", "breach", "malware",
        "ransomware", "phishing", "cybersecurity", "security", "hack"
    ]
    
    keyword_score = sum(1 for kw in cybersecurity_keywords if kw.lower() in excerpt.lower()) / len(cybersecurity_keywords)
    
    return (length_score * 0.4 + title_score * 0.3 + keyword_score * 0.3)

def _detect_blindspots(findings: list[dict[str, Any]], config: BALLMScoringConfig) -> list[BlindspotAnalysis]:
    """Detect blind spots and epistemic gaps in the findings."""
    blindspots = []
    
    # Coverage gap analysis
    if len(findings) < 3:
        blindspots.append(BlindspotAnalysis(
            type="coverage_gap",
            severity=0.8,
            description=f"Limited coverage - only {len(findings)} sources analyzed",
            evidence=[f"Total findings: {len(findings)}"],
            mitigation_suggestions=["Expand seed sources", "Increase collection depth"],
            epistemic_score=0.7
        ))
    
    # Recency gap analysis
    recent_findings = 0
    for f in findings:
        if f.get("fetched_at"):
            try:
                fetched = datetime.fromisoformat(f["fetched_at"].replace('Z', '+00:00'))
                if (datetime.now(UTC) - fetched).days < 7:
                    recent_findings += 1
            except Exception:
                pass
    
    if recent_findings < len(findings) * 0.5:
        blindspots.append(BlindspotAnalysis(
            type="recency_gap",
            severity=0.6,
            description="Many findings are outdated",
            evidence=[f"Recent findings: {recent_findings}/{len(findings)}"],
            mitigation_suggestions=["Refresh data collection", "Implement real-time monitoring"],
            epistemic_score=0.5
        ))
    
    # Confidence gap analysis
    low_confidence = sum(1 for f in findings if f.get("score", 0) < 0.5)
    if low_confidence > len(findings) * 0.3:
        blindspots.append(BlindspotAnalysis(
            type="confidence_gap",
            severity=0.7,
            description="Many findings have low confidence scores",
            evidence=[f"Low confidence findings: {low_confidence}/{len(findings)}"],
            mitigation_suggestions=["Improve source quality", "Enhance scoring algorithm"],
            epistemic_score=0.6
        ))
    
    # Assumption risk analysis
    assumptions = [
        "All sources are equally reliable",
        "Content freshness indicates relevance",
        "Domain reputation is static",
        "Text length correlates with quality"
    ]
    
    blindspots.append(BlindspotAnalysis(
        type="assumption_risk",
        severity=0.4,
        description="Scoring relies on several assumptions",
        evidence=assumptions,
        mitigation_suggestions=["Validate assumptions", "Implement dynamic scoring"],
        epistemic_score=0.4
    ))
    
    return blindspots

def _calculate_curiosity_amplification_index(blindspots: list[BlindspotAnalysis]) -> float:
    """Calculate the Curiosity Amplification Index (CAI)."""
    if not blindspots:
        return 0.0
    
    # CAI increases with the number and severity of identified blindspots
    total_severity = sum(bs.severity for bs in blindspots)
    avg_severity = total_severity / len(blindspots)
    
    # Normalize to 0-1 range
    cai = min(1.0, (len(blindspots) * 0.2 + avg_severity * 0.8))
    
    return cai

def _calculate_epistemic_humility(blindspots: list[BlindspotAnalysis], findings: list[dict[str, Any]]) -> float:
    """Calculate epistemic humility score based on awareness of limitations."""
    if not blindspots:
        return 0.0
    
    # Higher humility when more blindspots are identified
    humility_base = min(1.0, len(blindspots) * 0.2)
    
    # Adjust based on finding diversity
    domains = set(f.get("domain", "") for f in findings)
    diversity_bonus = min(0.2, len(domains) * 0.05)
    
    return min(1.0, humility_base + diversity_bonus)

def score_findings_ballm(
    findings: list[dict[str, Any]], 
    config: BALLMScoringConfig = DEFAULT_CONFIG
) -> dict[str, Any]:
    """
    Score findings using BALLM-aware approach with dual-layer output.
    
    Returns:
        Dict containing:
        - findings: scored findings
        - epistemic_meta_layer: blind spots and epistemic analysis
        - overall_epistemic_quality: composite epistemic score
    """
    if not findings:
        return {
            "findings": [],
            "epistemic_meta_layer": None,
            "overall_epistemic_quality": 0.0
        }
    
    # Score individual findings
    scored_findings = []
    for finding in findings:
        # Parse timestamp
        timestamp = None
        if finding.get("fetched_at"):
            try:
                timestamp = datetime.fromisoformat(finding["fetched_at"].replace('Z', '+00:00'))
            except Exception:
                pass
        
        # Calculate component scores
        source_score = _calculate_source_credibility(finding)
        content_score = _calculate_content_quality(finding)
        recency_score = _calculate_recency_score(timestamp)
        
        # Calculate base score
        base_score = (
            config.weights["source"] * source_score +
            config.weights["content"] * content_score +
            config.weights["recency"] * recency_score
        )
        
        # Add epistemic adjustments
        epistemic_bonus = 0.0
        if source_score < 0.7:
            epistemic_bonus += config.epistemic_params["humility_bonus"]
        if content_score < 0.6:
            epistemic_bonus += config.epistemic_params["uncertainty_penalty"]
        
        final_score = min(1.0, base_score + epistemic_bonus)
        
        # Store scoring breakdown
        finding["score"] = final_score
        finding["score_breakdown"] = {
            "base": base_score,
            "source": source_score,
            "content": content_score,
            "recency": recency_score,
            "epistemic_bonus": epistemic_bonus
        }
        
        scored_findings.append(finding)
    
    # Detect blindspots
    blindspots = _detect_blindspots(scored_findings, config)
    
    # Calculate epistemic metrics
    cai = _calculate_curiosity_amplification_index(blindspots)
    humility = _calculate_epistemic_humility(blindspots, scored_findings)
    
    # Create epistemic meta-layer
    meta_layer = EpistemicMetaLayer(
        blindspots=blindspots,
        assumptions=[
            "Source credibility is domain-based",
            "Content length indicates quality",
            "Recent content is more relevant"
        ],
        confidence_gaps=[
            f"Limited coverage: {len(scored_findings)} sources",
            f"Average confidence: {sum(f['score'] for f in scored_findings) / len(scored_findings):.2f}"
        ],
        curiosity_amplification_index=cai,
        epistemic_humility_score=humility,
        overall_epistemic_quality=(cai + humility) / 2
    )
    
    # Calculate overall epistemic quality
    overall_quality = (
        config.weights["epistemic"] * meta_layer.overall_epistemic_quality +
        (1 - config.weights["epistemic"]) * (sum(f["score"] for f in scored_findings) / len(scored_findings))
    )
    
    return {
        "findings": scored_findings,
        "epistemic_meta_layer": {
            "blindspots": [bs.__dict__ for bs in blindspots],
            "assumptions": meta_layer.assumptions,
            "confidence_gaps": meta_layer.confidence_gaps,
            "curiosity_amplification_index": cai,
            "epistemic_humility_score": humility,
            "overall_epistemic_quality": meta_layer.overall_epistemic_quality
        },
        "overall_epistemic_quality": overall_quality
    }