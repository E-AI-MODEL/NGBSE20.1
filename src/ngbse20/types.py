from __future__ import annotations

from typing import Any, Dict, List

Finding = Dict[str, Any]
Findings = List[Finding]
AssetScore = Dict[str, float]
AssetScores = Dict[str, AssetScore]

__all__ = ["Finding", "Findings", "AssetScore", "AssetScores"]
