"""
Integration tests for the complete NGBSE pipeline.
"""
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from src.ngbse20.runtime.orchestrator import PipelineOrchestrator


class TestPipelineIntegration:
    """Integration tests for the complete pipeline."""
    
    def test_pipeline_with_minimal_config(self):
        """Test pipeline with minimal configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test config files
            config_dir = Path(temp_dir) / "config"
            config_dir.mkdir()
            
            # Test seeds
            seeds_file = config_dir / "seeds.jsonl"
            with open(seeds_file, 'w') as f:
                f.write(json.dumps({"id": "test_seed", "type": "domain", "value": "example.com"}) + '\n')
            
            # Test rules
            rules_file = config_dir / "rules.json"
            with open(rules_file, 'w') as f:
                json.dump([], f)
            
            # Test config
            config_file = config_dir / "ngbse.config.yml"
            with open(config_file, 'w') as f:
                json.dump({
                    "output_dir": str(Path(temp_dir) / "output"),
                    "allowlist": ["*"],
                    "collectors": {"enabled": ["http_web"]}
                }, f)
            
            # Mock collectors to avoid external API calls
            with patch('src.ngbse20.runtime.collector_manager.HttpWebCollector') as mock_http:
                mock_instance = Mock()
                mock_instance.collect.return_value = [
                    {"id": "finding1", "type": "web", "confidence": 0.8}
                ]
                mock_http.return_value = mock_instance
                
                orchestrator = PipelineOrchestrator(str(config_dir))
                result = orchestrator.run_pipeline()
                
                assert result["status"] == "ok"
                assert len(result["findings"]) == 1
                assert result["findings"][0]["id"] == "finding1"
                assert "traces" in result
                assert "cai" in result
    
    def test_pipeline_with_hard_block(self):
        """Test pipeline with hard block rule."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir) / "config"
            config_dir.mkdir()
            
            # Test seeds
            seeds_file = config_dir / "seeds.jsonl"
            with open(seeds_file, 'w') as f:
                f.write(json.dumps({"id": "test_seed", "type": "domain", "value": "example.com"}) + '\n')
            
            # Test rules with hard block
            rules_file = config_dir / "rules.json"
            with open(rules_file, 'w') as f:
                json.dump([
                    {
                        "rule_id": "block1",
                        "action": {"type": "hard_block"},
                        "condition": "always_true"
                    }
                ], f)
            
            # Test config
            config_file = config_dir / "ngbse.config.yml"
            with open(config_file, 'w') as f:
                json.dump({
                    "output_dir": str(Path(temp_dir) / "output"),
                    "allowlist": ["*"],
                    "collectors": {"enabled": ["http_web"]}
                }, f)
            
            orchestrator = PipelineOrchestrator(str(config_dir))
            result = orchestrator.run_pipeline()
            
            assert result["status"] == "blocked"
            assert len(result["traces"]) == 1
            assert result["traces"][0]["event"] == "validate"
    
    def test_pipeline_output_files(self):
        """Test that pipeline creates expected output files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir) / "config"
            config_dir.mkdir()
            output_dir = Path(temp_dir) / "output"
            
            # Test seeds
            seeds_file = config_dir / "seeds.jsonl"
            with open(seeds_file, 'w') as f:
                f.write(json.dumps({"id": "test_seed", "type": "domain", "value": "example.com"}) + '\n')
            
            # Test rules
            rules_file = config_dir / "rules.json"
            with open(rules_file, 'w') as f:
                json.dump([], f)
            
            # Test config
            config_file = config_dir / "ngbse.config.yml"
            with open(config_file, 'w') as f:
                json.dump({
                    "output_dir": str(output_dir),
                    "allowlist": ["*"],
                    "collectors": {"enabled": ["http_web"]}
                }, f)
            
            # Mock collectors
            with patch('src.ngbse20.runtime.collector_manager.HttpWebCollector') as mock_http:
                mock_instance = Mock()
                mock_instance.collect.return_value = [
                    {"id": "finding1", "type": "web", "confidence": 0.8}
                ]
                mock_http.return_value = mock_instance
                
                orchestrator = PipelineOrchestrator(str(config_dir))
                result = orchestrator.run_pipeline()
                
                # Check that output files were created
                assert Path(result["output_files"]["findings"]).exists()
                assert Path(result["output_files"]["stix_bundle"]).exists()
                assert Path(result["output_files"]["history"]).exists()
                
                # Verify file contents
                with open(result["output_files"]["findings"], 'r') as f:
                    findings_data = json.load(f)
                    assert len(findings_data) == 1
                    assert findings_data[0]["id"] == "finding1"
    
    def test_pipeline_with_credentials(self):
        """Test pipeline with API credentials."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir) / "config"
            config_dir.mkdir()
            
            # Test seeds
            seeds_file = config_dir / "seeds.jsonl"
            with open(seeds_file, 'w') as f:
                f.write(json.dumps({"id": "test_seed", "type": "domain", "value": "example.com"}) + '\n')
            
            # Test rules
            rules_file = config_dir / "rules.json"
            with open(rules_file, 'w') as f:
                json.dump([], f)
            
            # Test config with multiple collectors
            config_file = config_dir / "ngbse.config.yml"
            with open(config_file, 'w') as f:
                json.dump({
                    "output_dir": str(Path(temp_dir) / "output"),
                    "allowlist": ["*"],
                    "collectors": {"enabled": ["http_web", "shodan", "censys"]}
                }, f)
            
            # Mock environment variables for credentials
            with patch.dict('os.environ', {
                'SHODAN_API_KEY': 'test_shodan_key',
                'CENSYS_API_ID': 'test_censys_id',
                'CENSYS_API_SECRET': 'test_censys_secret'
            }):
                # Mock collectors
                with patch('src.ngbse20.runtime.collector_manager.HttpWebCollector') as mock_http, \
                     patch('src.ngbse20.runtime.collector_manager.ShodanCollector') as mock_shodan, \
                     patch('src.ngbse20.runtime.collector_manager.CensysCollector') as mock_censys:
                    
                    # Setup mock instances
                    mock_http_instance = Mock()
                    mock_http_instance.collect.return_value = [{"id": "http_finding", "type": "web"}]
                    mock_http.return_value = mock_http_instance
                    
                    mock_shodan_instance = Mock()
                    mock_shodan_instance.api_key = "test_shodan_key"
                    mock_shodan_instance.collect.return_value = [{"id": "shodan_finding", "type": "shodan"}]
                    mock_shodan.return_value = mock_shodan_instance
                    
                    mock_censys_instance = Mock()
                    mock_censys_instance.api_id = "test_censys_id"
                    mock_censys_instance.collect.return_value = [{"id": "censys_finding", "type": "censys"}]
                    mock_censys.return_value = mock_censys_instance
                    
                    orchestrator = PipelineOrchestrator(str(config_dir))
                    result = orchestrator.run_pipeline()
                    
                    assert result["status"] == "ok"
                    # Should have findings from all three collectors
                    assert len(result["findings"]) == 3