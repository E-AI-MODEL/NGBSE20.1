"""
Test fixtures and sample data for NGBSE tests.
"""

from typing import Any, Dict, List


def get_sample_seeds() -> List[Dict[str, Any]]:
    """Get sample seeds for testing."""
    return [
        {
            "id": "seed_domain_1",
            "type": "domain",
            "value": "example.com",
            "metadata": {"source": "test", "confidence": 0.9},
        },
        {
            "id": "seed_ip_1",
            "type": "ip",
            "value": "1.2.3.4",
            "metadata": {"source": "test", "confidence": 0.8},
        },
        {
            "id": "seed_url_1",
            "type": "url",
            "value": "https://example.com/path",
            "metadata": {"source": "test", "confidence": 0.7},
        },
    ]


def get_sample_rules() -> List[Dict[str, Any]]:
    """Get sample rules for testing."""
    return [
        {
            "rule_id": "rule_warning_1",
            "name": "High Confidence Finding",
            "description": "Flag high confidence findings",
            "condition": "finding.confidence > 0.9",
            "action": {
                "type": "warning_flag",
                "message": "High confidence finding detected",
            },
        },
        {
            "rule_id": "rule_block_1",
            "name": "Block Test Domain",
            "description": "Block findings from test domains",
            "condition": "seed.value contains 'test'",
            "action": {"type": "hard_block", "message": "Test domain blocked"},
        },
    ]


def get_sample_findings() -> List[Dict[str, Any]]:
    """Get sample findings for testing."""
    return [
        {
            "id": "finding_1",
            "type": "web",
            "source": "http_web",
            "confidence": 0.85,
            "timestamp": "2024-01-01T00:00:00Z",
            "data": {
                "url": "https://example.com/page1",
                "title": "Example Page 1",
                "content": "Sample content",
            },
            "provenance": {"collector": "HttpWebCollector", "seed_id": "seed_domain_1"},
        },
        {
            "id": "finding_2",
            "type": "shodan",
            "source": "shodan",
            "confidence": 0.92,
            "timestamp": "2024-01-01T00:00:00Z",
            "data": {"ip": "1.2.3.4", "port": 80, "service": "http"},
            "provenance": {"collector": "ShodanCollector", "seed_id": "seed_ip_1"},
        },
    ]


def get_sample_config() -> Dict[str, Any]:
    """Get sample configuration for testing."""
    return {
        "output_dir": "test_output",
        "allowlist": ["*"],
        "collectors": {"enabled": ["http_web", "shodan", "censys", "leakix"]},
        "scoring": {
            "default_weights": {"coverage": 0.3, "recency": 0.3, "confidence": 0.4}
        },
        "ballm": {"enabled": True, "model": "gpt-4"},
    }


def get_sample_metrics() -> Dict[str, Any]:
    """Get sample metrics for testing."""
    return {
        "total_findings": 2,
        "high_confidence_findings": 1,
        "collectors_used": 2,
        "execution_time": 30.5,
    }


def get_sample_asset_scores() -> Dict[str, Any]:
    """Get sample asset scores for testing."""
    return {
        "example.com": {
            "overall_score": 0.85,
            "coverage_score": 0.8,
            "recency_score": 0.9,
            "confidence_score": 0.85,
            "last_updated": "2024-01-01T00:00:00Z",
        },
        "1.2.3.4": {
            "overall_score": 0.92,
            "coverage_score": 0.9,
            "recency_score": 0.95,
            "confidence_score": 0.92,
            "last_updated": "2024-01-01T00:00:00Z",
        },
    }


def get_sample_blindspots() -> Dict[str, Any]:
    """Get sample blindspots for testing."""
    return {
        "coverage": {
            "score": 0.2,
            "description": "Limited coverage of subdomains",
            "recommendations": ["Add more subdomain seeds", "Enable DNS enumeration"],
        },
        "recency": {
            "score": 0.3,
            "description": "Some findings are outdated",
            "recommendations": [
                "Increase collection frequency",
                "Focus on recent indicators",
            ],
        },
        "confidence": {
            "score": 0.1,
            "description": "Low confidence in some findings",
            "recommendations": ["Verify findings manually", "Use multiple sources"],
        },
    }


def get_sample_ballm_meta_layer() -> Dict[str, Any]:
    """Get sample BALLM meta-layer for testing."""
    return {
        "epistemic_humility_score": 0.75,
        "confidence_intervals": {
            "overall": [0.6, 0.9],
            "coverage": [0.1, 0.4],
            "recency": [0.2, 0.5],
        },
        "uncertainty_sources": [
            "Limited data from external APIs",
            "Potential false positives in automated collection",
            "Temporal gaps in monitoring",
        ],
        "recommendations": [
            "Increase manual verification of high-impact findings",
            "Implement additional validation layers",
            "Consider ensemble methods for scoring",
        ],
        "meta_insights": [
            "Current assessment has moderate confidence",
            "Coverage gaps may lead to missed threats",
            "Recent findings show higher reliability",
        ],
    }
