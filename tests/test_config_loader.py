import json
from pathlib import Path

import pytest

from ngbse20.config.loader import validate_files


def test_validate_files(tmp_path: Path):
    seeds = tmp_path / "seeds.json"
    rules = tmp_path / "rules.json"
    seeds.write_text(
        json.dumps({"id": "test_seed", "query": "https://example.com", "type": "web", "asset_id": "a1", "tags": ["x"]}),
        encoding="utf-8",
    )
    rules.write_text(
        json.dumps([{"id": "r1", "pattern": "example", "weight": 1.5}]),
        encoding="utf-8",
    )

    n_seeds, n_rules = validate_files(str(seeds), str(rules))
    assert n_seeds == 1
    assert n_rules == 1


def test_invalid_seed_url(tmp_path: Path):
    seeds = tmp_path / "seeds.json"
    rules = tmp_path / "rules.json"
    seeds.write_text(json.dumps({"id": "test_seed", "query": "not-a-url", "type": "web"}), encoding="utf-8")
    rules.write_text(json.dumps([]), encoding="utf-8")
    with pytest.raises(ValueError, match="url") as exc_info:
        validate_files(str(seeds), str(rules))

    error_msg = str(exc_info.value)
    assert "VALIDATION" not in error_msg  # ValueError met pydantic-inhoud
    assert "url" in error_msg
