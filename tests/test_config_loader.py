from ngbse20.config.loader import load_seeds, load_rules, validate_files
from pydantic import ValidationError
import json
from pathlib import Path

def test_validate_files(tmp_path: Path):
    seeds = tmp_path / "seeds.json"
    rules = tmp_path / "rules.json"
    seeds.write_text(json.dumps([{"url":"https://example.com","asset_id":"a1","tags":["x"]}]), encoding="utf-8")
    rules.write_text(json.dumps([{"id":"r1","pattern":"example","weight":1.5}]), encoding="utf-8")

    n_seeds, n_rules = validate_files(str(seeds), str(rules))
    assert n_seeds == 1 and n_rules == 1

def test_invalid_seed_url(tmp_path: Path):
    seeds = tmp_path / "seeds.json"
    rules = tmp_path / "rules.json"
    seeds.write_text(json.dumps([{"url":"not-a-url"}]), encoding="utf-8")
    rules.write_text(json.dumps([]), encoding="utf-8")
    try:
        validate_files(str(seeds), str(rules))
    except Exception as e:
        assert "VALIDATION" not in str(e)  # ValueError met pydantic-inhoud
        assert "url" in str(e)
