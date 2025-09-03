"""BALLM Meta-Layer Generator for NGBSE 20.1.

This module implements the core BALLM functionality: transforming blindspots into
epistemic insights and curiosity-generating questions using Large Language Models.
"""

from typing import Any, Dict, List
from .blindspot_interpreter import BlindspotInterpretationEngine
from .curiosity_generator import CuriosityGenerationEngine


class BALLMMetaLayerGenerator:
    """
    Generates the BALLM meta-layer that transforms blindspots into epistemic insights.
    """

    def __init__(self, llm_client):
        """Initialize BALLM generator with LLM client."""
        self.blindspot_interpreter = BlindspotInterpretationEngine(llm_client)
        self.curiosity_generator = CuriosityGenerationEngine(llm_client)

    def generate_meta_layer(
        self,
        findings: List[Dict[str, Any]],
        blindspots: Dict[str, Any],
        asset_scores: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate the complete BALLM meta-layer output."""

        # 1. Interpret blindspots with LLM
        blindspot_interpretation = (
            self.blindspot_interpreter.interpret_blindspots_with_llm(
                blindspots, findings
            )
        )

        # 2. Generate curiosity questions
        curiosity_questions = self.curiosity_generator.generate_curiosity_questions(
            findings, blindspots
        )

        # 3. Extract epistemic insights
        epistemic_insights = self.blindspot_interpreter.extract_epistemic_insights(
            blindspots, findings
        )

        # 4. Calculate epistemic humility
        epistemic_humility = self._calculate_epistemic_humility(findings, blindspots)

        # 5. Identify productive failures
        productive_failures = self._identify_productive_failures(blindspots, findings)

        return {
            "blindspot_interpretation": blindspot_interpretation,
            "epistemic_assumptions": epistemic_insights.get("assumptions", []),
            "curiosity_questions": curiosity_questions,
            "epistemic_confidence": epistemic_insights.get("confidence", 0.0),
            "productive_failure_insights": productive_failures,
            "epistemic_humility_score": epistemic_humility,
            "meta_layer_version": "1.0",
            "generation_timestamp": self._get_timestamp(),
        }

    def _calculate_epistemic_humility(
        self, findings: List[Dict[str, Any]], blindspots: Dict[str, Any]
    ) -> float:
        """Calculate epistemic humility score based on blindspot awareness."""
        # Base score starts at 0.5 (neutral)
        base_score = 0.5

        # Coverage gaps increase humility (we know we're missing things)
        coverage_imbalance = blindspots.get("coverage", {}).get("imbalance", 0.0)
        coverage_bonus = min(0.3, coverage_imbalance * 0.5)

        # Confidence gaps increase humility (we're uncertain)
        confidence_gaps = blindspots.get("confidence", {}).get("n", 0)
        confidence_bonus = min(0.2, confidence_gaps * 0.1)

        # Recency gaps increase humility (information might be outdated)
        recency_spike = blindspots.get("recency", {}).get("spike", False)
        recency_bonus = 0.1 if recency_spike else 0.0

        return min(1.0, base_score + coverage_bonus + confidence_bonus + recency_bonus)

    def _identify_productive_failures(
        self, blindspots: Dict[str, Any], findings: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Identify areas where 'failures' lead to productive learning."""
        productive_failures = []

        # Coverage gaps as productive failures
        coverage = blindspots.get("coverage", {})
        if coverage.get("imbalance", 0.0) > 0.5:
            productive_failures.append(
                {
                    "type": "coverage_gap",
                    "description": (
                        f"High source imbalance "
                        f"({coverage.get('max_category', 'Unknown')} dominates)"
                    ),
                    "learning_opportunity": "Diversify source types to reduce bias",
                    "productive_value": "High - reveals source bias",
                }
            )

        # Confidence gaps as productive failures
        confidence = blindspots.get("confidence", {})
        if confidence.get("n", 0) > 0:
            productive_failures.append(
                {
                    "type": "confidence_gap",
                    "description": f"{confidence.get('n', 0)} risky assets identified",
                    "learning_opportunity": (
                        "Investigate why high-score assets have low quality"
                    ),
                    "productive_value": "High - reveals scoring inconsistencies",
                }
            )

        # Recency gaps as productive failures
        recency = blindspots.get("recency", {})
        if recency.get("spike", False):
            productive_failures.append(
                {
                    "type": "recency_gap",
                    "description": "Temporal spike detected in findings",
                    "learning_opportunity": "Investigate what caused the spike",
                    "productive_value": "Medium - reveals temporal patterns",
                }
            )

        return productive_failures

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime, timezone

        return datetime.now(timezone.utc).isoformat()
