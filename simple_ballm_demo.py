#!/usr/bin/env python3
"""
Simple BALLM Demo - No external dependencies required.
"""

import json
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, 'src')

# Mock LLM client for demo
class MockLLMClient:
    def call(self, system_prompt, user_prompt, max_tokens=400, temperature=0.3):
        return "Mock LLM response: This is a demonstration of BALLM functionality."

# Mock the LLM client import
sys.modules['ngbse20.llm_client'] = type('MockModule', (), {'LLMClient': MockLLMClient})()

from ngbse20.ballm.meta_layer_generator import BALLMMetaLayerGenerator


def create_sample_data():
    """Create sample findings and blindspots for demonstration."""
    
    findings = [
        {
            "id": "finding-1",
            "score": 0.85,
            "asset": "example.com",
            "source": {"type": "web", "url": "https://example.com", "domain": "example.com"},
            "timestamp": "2025-01-15T10:00:00Z",
            "quality": {"q": 0.8}
        },
        {
            "id": "finding-2", 
            "score": 0.72,
            "asset": "test.org",
            "source": {"type": "news", "url": "https://test.org/article", "domain": "test.org"},
            "timestamp": "2025-01-15T11:00:00Z",
            "quality": {"q": 0.6}
        },
        {
            "id": "finding-3",
            "score": 0.91,
            "asset": "demo.net",
            "source": {"type": "web", "url": "https://demo.net", "domain": "demo.net"},
            "timestamp": "2025-01-15T12:00:00Z",
            "quality": {"q": 0.4}  # High score but low quality
        }
    ]
    
    blindspots = {
        "coverage": {
            "ratios": {"web": 0.67, "news": 0.33},
            "max_category": "web",
            "imbalance": 0.34
        },
        "recency": {
            "spike": True,
            "detail": {"2025-01-15": 3}
        },
        "confidence": {
            "risky_assets": ["demo.net"],
            "n": 1
        }
    }
    
    asset_scores = {
        "example.com": {"avg_e_ai_star": 0.85},
        "test.org": {"avg_e_ai_star": 0.72},
        "demo.net": {"avg_e_ai_star": 0.91}
    }
    
    return findings, blindspots, asset_scores


def demo_ballm_analysis():
    """Demonstrate BALLM analysis."""
    
    print("🚀 NGBSE 20.1 BALLM Demo (Simple Version)")
    print("=" * 60)
    
    # Create sample data
    findings, blindspots, asset_scores = create_sample_data()
    
    print("\n📊 Sample Data:")
    print(f"- Findings: {len(findings)} items")
    print(f"- Blindspots detected: {len(blindspots)} types")
    print(f"- Assets analyzed: {len(asset_scores)}")
    
    print("\n🔍 Raw Blindspots (what existing NGBSE detects):")
    print(json.dumps(blindspots, indent=2))
    
    # Initialize BALLM engine
    print("\n🧠 Initializing BALLM Engine...")
    try:
        llm_client = MockLLMClient()
        ballm_generator = BALLMMetaLayerGenerator(llm_client)
        print("✅ BALLM Engine initialized successfully")
    except Exception as e:
        print(f"❌ Error initializing BALLM: {e}")
        return
    
    # Generate BALLM meta-layer
    print("\n🔬 Generating BALLM Meta-Layer...")
    try:
        meta_layer = ballm_generator.generate_meta_layer(findings, blindspots, asset_scores)
        print("✅ BALLM Meta-Layer generated successfully")
    except Exception as e:
        print(f"❌ Error generating meta-layer: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Display results
    print("\n🎯 BALLM Results:")
    print("=" * 60)
    
    # Epistemic Humility Score
    humility = meta_layer.get("epistemic_humility_score", 0.0)
    print(f"\n🧎 Epistemic Humility Score: {humility:.3f}")
    if humility > 0.7:
        print("   → High awareness of knowledge limitations")
    elif humility > 0.5:
        print("   → Moderate awareness of knowledge limitations")
    else:
        print("   → Low awareness of knowledge limitations")
    
    # Blindspot Interpretation
    interpretation = meta_layer.get("blindspot_interpretation", {})
    print(f"\n🔍 Blindspot Interpretation:")
    print(f"   Method: {interpretation.get('interpretation_method', 'N/A')}")
    print(f"   Confidence: {interpretation.get('confidence_level', 0.0):.3f}")
    
    # Curiosity Questions
    questions = meta_layer.get("curiosity_questions", [])
    print(f"\n❓ Curiosity Questions Generated: {len(questions)}")
    for i, q in enumerate(questions[:3], 1):  # Show first 3
        print(f"   {i}. [{q.get('type', 'unknown')}] {q.get('question', 'N/A')}")
        print(f"      Value: {q.get('exploration_value', 'N/A')}")
    
    # Epistemic Insights
    insights = meta_layer.get("epistemic_assumptions", [])
    print(f"\n💡 Epistemic Assumptions Identified: {len(insights)}")
    for insight in insights:
        print(f"   - {insight}")
    
    # Productive Failures
    failures = meta_layer.get("productive_failure_insights", [])
    print(f"\n🎓 Productive Failures (Learning Opportunities): {len(failures)}")
    for failure in failures:
        print(f"   - {failure.get('type', 'unknown')}: {failure.get('description', 'N/A')}")
        print(f"     Learning: {failure.get('learning_opportunity', 'N/A')}")
    
    # Save results
    output_file = "demo_ballm_results.json"
    with open(output_file, 'w') as f:
        json.dump(meta_layer, f, indent=2, ensure_ascii=False)
    print(f"\n💾 Results saved to: {output_file}")
    
    print("\n🎉 BALLM Demo Complete!")
    print("\nThis demonstrates how BALLM transforms raw blindspot data into:")
    print("- Epistemic insights and awareness")
    print("- Curiosity-driven questions for exploration")
    print("- Productive failure identification")
    print("- Quantified epistemic humility")
    
    print("\n🔧 To use with real LLM:")
    print("1. Configure API keys in .env file")
    print("2. Run: ngbse20 ballm-analyze --findings <path> --out <path>")


if __name__ == "__main__":
    demo_ballm_analysis()