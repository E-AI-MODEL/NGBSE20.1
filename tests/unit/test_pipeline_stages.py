"""
Unit tests for PipelineStages.
"""

from unittest.mock import Mock, patch

from src.ngbse20.runtime.pipeline_stages import PipelineStages


class TestPipelineStages:
    """Test cases for PipelineStages."""

    def test_validate_stage_blocked(self):
        """Test validation stage with hard block."""
        stages = PipelineStages("test_output")

        rules = [
            {
                "rule_id": "block1",
                "action": {"type": "hard_block"},
                "condition": "always_true",
            }
        ]
        metrics = {}

        with patch("src.ngbse20.runtime.pipeline_stages.evaluate_rules") as mock_eval:
            mock_eval.return_value = [{"rule_id": "block1"}]

            result = stages.validate_stage(rules, metrics)

            assert result["status"] == "blocked"
            assert "trace" in result

    def test_validate_stage_ok(self):
        """Test validation stage without blocks."""
        stages = PipelineStages("test_output")

        rules = [
            {
                "rule_id": "warn1",
                "action": {"type": "warning"},
                "condition": "always_true",
            }
        ]
        metrics = {}

        with patch("src.ngbse20.runtime.pipeline_stages.evaluate_rules") as mock_eval:
            mock_eval.return_value = []  # No blocks

            result = stages.validate_stage(rules, metrics)

            assert result["status"] == "ok"

    def test_collect_stage(self):
        """Test collection stage."""
        stages = PipelineStages("test_output")

        seeds = [{"id": "seed1", "type": "domain", "value": "example.com"}]

        mock_collector = Mock()
        mock_collector.collect.return_value = [
            {"id": "finding1", "type": "web"},
            {"id": "finding2", "type": "web"},
        ]
        collectors = [mock_collector]

        result = stages.collect_stage(seeds, collectors)

        assert len(result["findings"]) == 2
        assert result["findings"][0]["id"] == "finding1"
        assert "trace" in result

    def test_scoring_stage(self):
        """Test scoring stage."""
        stages = PipelineStages("test_output")

        findings = [
            {"id": "finding1", "type": "web", "confidence": 0.8},
            {"id": "finding2", "type": "web", "confidence": 0.6},
        ]

        with patch("src.ngbse20.runtime.pipeline_stages.score_findings") as mock_score:
            mock_score.return_value = findings  # Assume no changes for simplicity

            result = stages.scoring_stage(findings)

            assert len(result["scored_findings"]) == 2
            assert "trace" in result

    def test_ballm_stage_success(self):
        """Test BALLM stage with successful generation."""
        stages = PipelineStages("test_output")

        scored_findings = [{"id": "finding1", "type": "web"}]
        blindspots = {"coverage": 0.2, "recency": 0.3, "confidence": 0.1}
        asset_scores = {"asset1": 0.8}

        mock_meta_layer = {
            "epistemic_humility_score": 0.7,
            "insights": ["test insight"],
        }

        with patch(
            "src.ngbse20.runtime.pipeline_stages.BALLMMetaLayerGenerator"
        ) as mock_generator_class:
            mock_generator = Mock()
            mock_generator.generate_meta_layer.return_value = mock_meta_layer
            mock_generator_class.return_value = mock_generator

            result = stages.ballm_stage(scored_findings, blindspots, asset_scores)

            assert result["meta_layer"] == mock_meta_layer
            assert "trace" in result

    def test_ballm_stage_failure(self):
        """Test BALLM stage with failure."""
        stages = PipelineStages("test_output")

        scored_findings = [{"id": "finding1", "type": "web"}]
        blindspots = {"coverage": 0.2, "recency": 0.3, "confidence": 0.1}
        asset_scores = {"asset1": 0.8}

        with patch(
            "src.ngbse20.runtime.pipeline_stages.BALLMMetaLayerGenerator"
        ) as mock_generator_class:
            mock_generator = Mock()
            mock_generator.generate_meta_layer.side_effect = Exception("BALLM failed")
            mock_generator_class.return_value = mock_generator

            result = stages.ballm_stage(scored_findings, blindspots, asset_scores)

            assert "error" in result["meta_layer"]
            assert result["meta_layer"]["error"] == "BALLM failed"
            assert "trace" in result
