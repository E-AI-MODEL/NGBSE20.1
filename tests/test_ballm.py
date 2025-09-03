"""Tests for BALLM functionality."""

import pytest
from unittest.mock import Mock
from ngbse20.ballm.meta_layer_generator import BALLMMetaLayerGenerator
from ngbse20.ballm.blindspot_interpreter import BlindspotInterpretationEngine
from ngbse20.ballm.curiosity_generator import CuriosityGenerationEngine


class TestBALLMMetaLayerGenerator:
    """Test BALLM Meta-Layer Generator."""
    
    def test_init(self):
        """Test initialization."""
        mock_llm = Mock()
        generator = BALLMMetaLayerGenerator(mock_llm)
        
        assert generator.blindspot_interpreter is not None
        assert generator.curiosity_generator is not None
    
    def test_generate_meta_layer(self):
        """Test meta-layer generation."""
        mock_llm = Mock()
        generator = BALLMMetaLayerGenerator(mock_llm)
        
        # Mock the sub-engines
        generator.blindspot_interpreter.interpret_blindspots_with_llm = Mock(
            return_value={"interpretation": "test", "confidence": 0.8}
        )
        generator.curiosity_generator.generate_curiosity_questions = Mock(
            return_value=[{"question": "test question"}]
        )
        generator.blindspot_interpreter.extract_epistemic_insights = Mock(
            return_value={"assumptions": [], "confidence": 0.7}
        )
        
        findings = [{"score": 0.8, "asset": "test.com"}]
        blindspots = {
            "coverage": {"imbalance": 0.3, "ratios": {"Web": 0.7, "News": 0.3}},
            "recency": {"spike": False, "detail": {}},
            "confidence": {"n": 0, "risky_assets": []}
        }
        asset_scores = {"test.com": {"avg_e_ai_star": 0.8}}
        
        result = generator.generate_meta_layer(findings, blindspots, asset_scores)
        
        assert "blindspot_interpretation" in result
        assert "curiosity_questions" in result
        assert "epistemic_humility_score" in result
        assert "meta_layer_version" in result
        assert result["meta_layer_version"] == "1.0"
    
    def test_epistemic_humility_calculation(self):
        """Test epistemic humility calculation."""
        mock_llm = Mock()
        generator = BALLMMetaLayerGenerator(mock_llm)
        
        # Test with high imbalance
        blindspots = {
            "coverage": {"imbalance": 0.8},
            "recency": {"spike": True},
            "confidence": {"n": 5}
        }
        
        humility = generator._calculate_epistemic_humility([], blindspots)
        assert humility > 0.5  # Should be higher due to blindspots
    
    def test_productive_failures_identification(self):
        """Test productive failures identification."""
        mock_llm = Mock()
        generator = BALLMMetaLayerGenerator(mock_llm)
        
        blindspots = {
            "coverage": {"imbalance": 0.7, "max_category": "Web"},
            "recency": {"spike": True},
            "confidence": {"n": 3}
        }
        
        failures = generator._identify_productive_failures(blindspots, [])
        assert len(failures) > 0
        assert any(f["type"] == "coverage_gap" for f in failures)


class TestBlindspotInterpretationEngine:
    """Test Blindspot Interpretation Engine."""
    
    def test_init(self):
        """Test initialization."""
        mock_llm = Mock()
        engine = BlindspotInterpretationEngine(mock_llm)
        assert engine.llm_client == mock_llm
    
    def test_extract_epistemic_insights(self):
        """Test epistemic insights extraction."""
        mock_llm = Mock()
        engine = BlindspotInterpretationEngine(mock_llm)
        
        blindspots = {
            "coverage": {"imbalance": 0.6, "max_category": "Web"},
            "recency": {"spike": False},
            "confidence": {"n": 0}
        }
        findings = [{"score": 0.8}]
        
        insights = engine.extract_epistemic_insights(blindspots, findings)
        
        assert "assumptions" in insights
        assert "confidence" in insights
        assert "knowledge_gaps" in insights
        assert "epistemic_biases" in insights


class TestCuriosityGenerationEngine:
    """Test Curiosity Generation Engine."""
    
    def test_init(self):
        """Test initialization."""
        mock_llm = Mock()
        engine = CuriosityGenerationEngine(mock_llm)
        assert engine.llm_client == mock_llm
    
    def test_generate_coverage_curiosity_questions(self):
        """Test coverage-based curiosity questions."""
        mock_llm = Mock()
        engine = CuriosityGenerationEngine(mock_llm)
        
        blindspots = {
            "coverage": {
                "imbalance": 0.7,
                "max_category": "Web",
                "ratios": {"Web": 0.8, "News": 0.2}
            }
        }
        
        questions = engine._generate_coverage_curiosity_questions(blindspots)
        assert len(questions) > 0
        assert any(q["type"] == "coverage_gap" for q in questions)
    
    def test_generate_productive_failure_questions(self):
        """Test productive failure questions."""
        mock_llm = Mock()
        engine = CuriosityGenerationEngine(mock_llm)
        
        blindspots = {
            "coverage": {"imbalance": 0.7},
            "confidence": {"n": 3},
            "recency": {"spike": True}
        }
        
        questions = engine._generate_productive_failure_questions(blindspots)
        assert len(questions) > 0
        assert any(q["type"] == "productive_failure" for q in questions)


if __name__ == "__main__":
    pytest.main([__file__])