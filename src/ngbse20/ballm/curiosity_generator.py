"""Curiosity Generation Engine for BALLM.

This engine generates curiosity-driven questions based on blindspots and findings.
"""

from __future__ import annotations

import re
from typing import Any


class CuriosityGenerationEngine:
    """Generates curiosity-driven questions based on blindspots and findings."""

    def __init__(self, llm_client: Any) -> None:
        """Initialize with LLM client."""
        self.llm_client = llm_client

    def generate_curiosity_questions(
        self, findings: list[dict[str, Any]], blindspots: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Generate curiosity-driven questions based on blindspots and findings."""

        questions = []

        # 1. Coverage-based curiosity questions
        coverage_questions = self._generate_coverage_curiosity_questions(blindspots)
        questions.extend(coverage_questions)

        # 2. Recency-based curiosity questions
        recency_questions = self._generate_recency_curiosity_questions(blindspots)
        questions.extend(recency_questions)

        # 3. Confidence-based curiosity questions
        confidence_questions = self._generate_confidence_curiosity_questions(blindspots)
        questions.extend(confidence_questions)

        # 4. LLM-generated curiosity questions
        llm_questions = self._generate_llm_curiosity_questions(findings, blindspots)
        questions.extend(llm_questions)

        # 5. Productive failure questions
        failure_questions = self._generate_productive_failure_questions(blindspots)
        questions.extend(failure_questions)

        return questions[:10]  # Limit to top 10 questions

    def _fallback_confidence_questions(self) -> list[dict[str, Any]]:
        """Fallback questions for confidence gaps when inputs are insufficient."""
        return [
            {
                "type": "confidence_gap",
                "question": ("What data quality issues might reduce confidence in these findings?"),
                "curiosity_level": "high",
                "exploration_value": "High - raises overall evidence quality",
                "category": "data_quality",
            },
            {
                "type": "confidence_gap",
                "question": ("Which sources should be re-validated to improve reliability and attribution?"),
                "curiosity_level": "medium",
                "exploration_value": "Medium - improves source reliability",
                "category": "source_reliability",
            },
        ]

    def _generate_coverage_curiosity_questions(self, blindspots: dict[str, Any]) -> list[dict[str, Any]]:
        """Generate questions based on coverage gaps."""
        questions = []
        coverage = blindspots.get("coverage", {})

        ratios = coverage.get("ratios", {})
        max_category = coverage.get("max_category", "")
        imbalance = coverage.get("imbalance", 0.0)

        if imbalance > 0.5:
            questions.append(
                {
                    "type": "coverage_gap",
                    "question": f"What are we missing by relying heavily on {max_category} sources?",
                    "curiosity_level": "high",
                    "exploration_value": "High - reveals source bias",
                    "category": "source_diversity",
                }
            )

        if ratios:
            underrepresented = [cat for cat, ratio in ratios.items() if ratio < 0.1]
            for cat in underrepresented:
                questions.append(
                    {
                        "type": "coverage_gap",
                        "question": f"What insights might {cat} sources provide that we're missing?",
                        "curiosity_level": "medium",
                        "exploration_value": "Medium - diversifies perspective",
                        "category": "source_diversity",
                    }
                )

        return questions

    def _generate_recency_curiosity_questions(self, blindspots: dict[str, Any]) -> list[dict[str, Any]]:
        """Generate questions based on recency gaps."""
        questions = []
        recency = blindspots.get("recency", {})

        spike = recency.get("spike", False)
        detail = recency.get("detail", {})

        if spike:
            questions.append(
                {
                    "type": "recency_gap",
                    "question": "What event or development caused this temporal spike in findings?",
                    "curiosity_level": "high",
                    "exploration_value": "High - reveals causal factors",
                    "category": "temporal_analysis",
                }
            )

        if detail:
            # Find gaps in temporal coverage
            days = sorted(detail.keys())
            if len(days) > 1:
                questions.append(
                    {
                        "type": "recency_gap",
                        "question": "What happened during the periods with no findings?",
                        "curiosity_level": "medium",
                        "exploration_value": "Medium - reveals temporal gaps",
                        "category": "temporal_analysis",
                    }
                )

        return questions

    def _generate_confidence_curiosity_questions(self, blindspots: dict[str, Any]) -> list[dict[str, Any]]:
        """Generate questions based on confidence gaps."""
        questions = []
        confidence = blindspots.get("confidence", {})

        risky_assets = confidence.get("risky_assets", [])
        n_risky = confidence.get("n", 0)

        if n_risky > 0:
            questions.append(
                {
                    "type": "confidence_gap",
                    "question": f"Why do {n_risky} assets have high scores but low quality?",
                    "curiosity_level": "high",
                    "exploration_value": "High - reveals scoring inconsistencies",
                    "category": "quality_assessment",
                }
            )

            if risky_assets:
                questions.append(
                    {
                        "type": "confidence_gap",
                        "question": f"What makes {risky_assets[0]} both high-risk and low-quality?",
                        "curiosity_level": "medium",
                        "exploration_value": "Medium - investigates specific cases",
                        "category": "quality_assessment",
                    }
                )

        return questions or self._fallback_confidence_questions()

    def _generate_llm_curiosity_questions(
        self, findings: list[dict[str, Any]], blindspots: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Generate curiosity questions using LLM."""

        prompt = self._create_curiosity_prompt(findings, blindspots)

        try:
            response = self.llm_client.call(
                "You are a curiosity-driven researcher. Generate probing questions.",
                prompt,
                max_tokens=300,
                temperature=0.4,
            )

            if response:
                return self._parse_llm_curiosity_questions(response)
        except Exception:
            pass

        return []

    def _create_curiosity_prompt(self, findings: list[dict[str, Any]], blindspots: dict[str, Any]) -> str:
        """Create prompt for LLM curiosity generation."""
        min_score = min([f.get("score", 0.0) for f in findings], default=0.0)
        max_score = max([f.get("score", 0.0) for f in findings], default=0.0)
        asset_types = list(set(f.get("asset", "") for f in findings))

        return f"""
        Based on these findings and blindspots, generate 3 curiosity-driven questions:

        FINDINGS SUMMARY:
        - Total findings: {len(findings)}
        - Asset types: {asset_types}
        - Score range: {min_score:.2f} - {max_score:.2f}

        BLINDSPOTS IDENTIFIED:
        - Coverage gaps: {blindspots.get('coverage', {}).get('imbalance', 0.0):.3f}
        - Recency spike: {blindspots.get('recency', {}).get('spike', False)}
        - Confidence gaps: {blindspots.get('confidence', {}).get('n', 0)}

        Generate questions that:
        1. Explore the unknown areas (coverage gaps)
        2. Investigate temporal patterns (recency gaps)
        3. Probe confidence boundaries (confidence gaps)
        4. Challenge our assumptions
        5. Lead to productive failure and learning

        Format each question to start with "What if..." or "How might..." or
        "Why does..."
        Make them specific and actionable for further investigation.
        """

    def _parse_llm_curiosity_questions(self, response: str) -> list[dict[str, Any]]:
        """Parse LLM response into structured curiosity questions."""
        questions = []

        # Simple parsing - look for question patterns
        lines = response.split("\n")
        for line in lines:
            stripped_line = line.strip()
            # Models routinely number their answers ("1. How might...").
            # Strip only list markers, not free text or arbitrary commentary.
            question_line = re.sub(r"^(?:\d{1,3}[.)]\s+|[-*]\s+)", "", stripped_line)
            if question_line and any(
                question_line.startswith(prefix)
                for prefix in ["What if", "How might", "Why does", "What are", "How do"]
            ):
                questions.append(
                    {
                        "type": "llm_generated",
                        "question": question_line,
                        "curiosity_level": "high",
                        "exploration_value": "High - LLM-generated insight",
                        "category": "llm_insight",
                    }
                )

        return questions[:3]  # Limit to 3 LLM questions

    def _generate_productive_failure_questions(self, blindspots: dict[str, Any]) -> list[dict[str, Any]]:
        """Generate questions that turn failures into learning opportunities."""
        questions = []

        # Coverage failures as learning opportunities
        coverage = blindspots.get("coverage", {})
        if coverage.get("imbalance", 0.0) > 0.6:
            questions.append(
                {
                    "type": "productive_failure",
                    "question": "How can we use this source bias to improve our collection strategy?",
                    "curiosity_level": "high",
                    "exploration_value": "High - turns bias into improvement",
                    "category": "learning_opportunity",
                }
            )

        # Confidence failures as learning opportunities
        confidence = blindspots.get("confidence", {})
        if confidence.get("n", 0) > 0:
            questions.append(
                {
                    "type": "productive_failure",
                    "question": "What can we learn from the mismatch between scores and quality?",
                    "curiosity_level": "high",
                    "exploration_value": "High - improves scoring methodology",
                    "category": "learning_opportunity",
                }
            )

        # Recency failures as learning opportunities
        recency = blindspots.get("recency", {})
        if recency.get("spike", False):
            questions.append(
                {
                    "type": "productive_failure",
                    "question": ("How can we harden processes to withstand news-driven spikes in activity?"),
                    "curiosity_level": "medium",
                    "exploration_value": "Medium - identifies process resilience gaps",
                    "category": "learning_opportunity",
                }
            )

        return questions or self._fallback_productive_failure_questions()

    def _fallback_productive_failure_questions(self) -> list[dict[str, Any]]:
        """Fallback questions when LLM or heuristics provide no results."""
        return [
            {
                "type": "productive_failure",
                "question": ("Which security controls may have failed given the observed findings, and why?"),
                "curiosity_level": "high",
                "exploration_value": "High - uncovers mitigation gaps",
                "category": "mitigation_failure",
            },
            {
                "type": "productive_failure",
                "question": ("Where did incident response appear inadequate, and what evidence supports that?"),
                "curiosity_level": "medium",
                "exploration_value": "Medium - improves response procedures",
                "category": "process_gap",
            },
        ]
