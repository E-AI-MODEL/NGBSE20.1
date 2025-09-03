"""Blindspot Interpretation Engine for BALLM.

This engine uses LLM to interpret blindspots and extract deeper epistemic insights.
"""

from __future__ import annotations

from typing import Any, Dict, List


class BlindspotInterpretationEngine:
    """Interprets blindspots using LLM to extract epistemic insights."""

    def __init__(self, llm_client: Any) -> None:
        """Initialize with LLM client."""
        self.llm_client = llm_client

    def interpret_blindspots_with_llm(
        self, blindspots: Dict[str, Any], findings: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Use LLM to interpret what blindspots mean epistemically."""

        # Create comprehensive prompt for LLM interpretation
        prompt = self._create_interpretation_prompt(blindspots, findings)

        # Get LLM interpretation
        interpretation = (
            self.llm_client.call(
                "You are an epistemic analyst. Analyze blindspots for deeper insights.",
                prompt,
                max_tokens=400,
                temperature=0.3,
            )
            or "Unable to interpret blindspots with LLM."
        )

        return {
            "interpretation": interpretation,
            "epistemic_insights": self._extract_epistemic_insights_from_text(interpretation),
            "confidence_level": self._assess_interpretation_confidence(blindspots),
            "interpretation_method": "llm_analysis",
        }

    def extract_epistemic_insights(self, blindspots: Dict[str, Any], findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract epistemic insights from blindspots and findings."""

        insights = {
            "assumptions": self._identify_hidden_assumptions(blindspots, findings),
            "confidence": self._calculate_overall_confidence(findings, blindspots),
            "knowledge_gaps": self._identify_knowledge_gaps(blindspots, findings),
            "epistemic_biases": self._identify_epistemic_biases(blindspots, findings),
        }

        return insights

    def _create_interpretation_prompt(self, blindspots: Dict[str, Any], findings: List[Dict[str, Any]]) -> str:
        """Create comprehensive prompt for LLM interpretation."""

        return f"""
        Analyze these blindspots from an epistemic perspective:

        COVERAGE GAPS:
        - Source distribution: {blindspots.get('coverage', {}).get('ratios', {})}
        - Max category: {blindspots.get('coverage', {}).get('max_category', 'Unknown')}
        - Imbalance score: {blindspots.get('coverage', {}).get('imbalance', 0.0):.3f}

        What does this source imbalance reveal about our knowledge?
        Which perspectives are we missing?

        RECENCY GAPS:
        - Temporal spike: {blindspots.get('recency', {}).get('spike', False)}
        - Day distribution: {blindspots.get('recency', {}).get('detail', {})}

        What do temporal patterns suggest about information freshness?
        Are we missing recent developments?

        CONFIDENCE GAPS:
        - Risky assets: {blindspots.get('confidence', {}).get('risky_assets', [])}
        - Count: {blindspots.get('confidence', {}).get('n', 0)}

        What does the confidence distribution reveal about our certainty?
        Where should we be more humble about our knowledge?

        CONTEXT:
        - Total findings: {len(findings)}
        - Asset types: {list(set(f.get('asset', '') for f in findings))}

        Provide epistemic insights in 3-4 sentences, focusing on:
        1. What these gaps reveal about our knowledge
        2. Potential biases or blind spots
        3. Areas where we should be epistemically humble
        """

    def _extract_epistemic_insights_from_text(self, text: str) -> List[str]:
        """Extract key epistemic insights from LLM response."""
        # Simple extraction - in production this could be more sophisticated
        insights = []

        # Look for key phrases that indicate epistemic insights
        key_phrases = [
            "bias",
            "blind spot",
            "missing",
            "uncertain",
            "humble",
            "assumption",
            "gap",
            "incomplete",
            "partial",
        ]

        for phrase in key_phrases:
            if phrase.lower() in text.lower():
                insights.append(f"Identified {phrase} in analysis")

        if not insights:
            insights.append("LLM provided general interpretation")

        return insights

    def _assess_interpretation_confidence(self, blindspots: Dict[str, Any]) -> float:
        """Assess confidence in the interpretation based on blindspot quality."""
        confidence = 0.5  # Base confidence

        # More blindspots = higher confidence in interpretation
        total_gaps = sum(
            [
                len(blindspots.get("coverage", {}).get("ratios", {})),
                len(blindspots.get("recency", {}).get("detail", {})),
                blindspots.get("confidence", {}).get("n", 0),
            ]
        )

        if total_gaps > 0:
            confidence += min(0.3, total_gaps * 0.1)

        # High imbalance suggests clearer interpretation
        coverage_imbalance = blindspots.get("coverage", {}).get("imbalance", 0.0)
        if coverage_imbalance > 0.5:
            confidence += 0.2

        return min(1.0, confidence)

    def _identify_hidden_assumptions(self, blindspots: Dict[str, Any], findings: List[Dict[str, Any]]) -> List[str]:
        """Identify hidden assumptions in our analysis."""
        assumptions = []

        # Coverage assumptions
        coverage = blindspots.get("coverage", {})
        if coverage.get("max_category"):
            assumptions.append(f"Assuming {coverage['max_category']} sources are representative")

        # Recency assumptions
        recency = blindspots.get("recency", {})
        if not recency.get("spike"):
            assumptions.append("Assuming information is temporally distributed")

        # Confidence assumptions
        if findings:
            avg_score = sum(f.get("score", 0.0) for f in findings) / len(findings)
            if avg_score > 0.7:
                assumptions.append("Assuming high scores indicate high confidence")

        return assumptions

    def _calculate_overall_confidence(self, findings: List[Dict[str, Any]], blindspots: Dict[str, Any]) -> float:
        """Calculate overall epistemic confidence."""
        if not findings:
            return 0.0

        # Base confidence from findings quality
        avg_score = sum(f.get("score", 0.0) for f in findings) / len(findings)
        base_confidence = avg_score * 0.6

        # Reduce confidence based on blindspots
        blindspot_penalty = 0.0

        # Coverage penalty
        coverage_imbalance = blindspots.get("coverage", {}).get("imbalance", 0.0)
        blindspot_penalty += coverage_imbalance * 0.2

        # Confidence gaps penalty
        confidence_gaps = blindspots.get("confidence", {}).get("n", 0)
        blindspot_penalty += min(0.3, confidence_gaps * 0.1)

        return max(0.0, base_confidence - blindspot_penalty)

    def _identify_knowledge_gaps(self, blindspots: Dict[str, Any], findings: List[Dict[str, Any]]) -> List[str]:
        """Identify specific knowledge gaps."""
        gaps = []

        # Source coverage gaps
        coverage = blindspots.get("coverage", {})
        ratios = coverage.get("ratios", {})
        if ratios:
            min_source = min(ratios.items(), key=lambda x: x[1])
            if min_source[1] < 0.1:  # Less than 10%
                gaps.append(f"Limited coverage in {min_source[0]} sources")

        # Temporal gaps
        recency = blindspots.get("recency", {})
        if recency.get("spike"):
            gaps.append("Temporal clustering suggests missing historical context")

        # Quality gaps
        confidence = blindspots.get("confidence", {})
        if confidence.get("n", 0) > 0:
            gaps.append("High-risk assets with low quality scores")

        return gaps

    def _identify_epistemic_biases(self, blindspots: Dict[str, Any], findings: List[Dict[str, Any]]) -> List[str]:
        """Identify potential epistemic biases."""
        biases = []

        # Source bias
        coverage = blindspots.get("coverage", {})
        max_category = coverage.get("max_category", "")
        if max_category and coverage.get("imbalance", 0.0) > 0.6:
            biases.append(f"Over-reliance on {max_category} sources")

        # Recency bias
        recency = blindspots.get("recency", {})
        if recency.get("spike"):
            biases.append("Temporal bias toward recent information")

        # Quality bias
        if findings:
            high_scores = [f for f in findings if f.get("score", 0.0) > 0.8]
            if len(high_scores) > len(findings) * 0.7:
                biases.append("Potential overconfidence in scoring")

        return biases
