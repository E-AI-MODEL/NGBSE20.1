from types import SimpleNamespace

from ngbse20.runtime.orchestrator import run_pipeline


def fake_get(url, timeout=15, headers=None):
    return SimpleNamespace(text="<html><title>Test</title></html>", status_code=200)


def test_run_pipeline(monkeypatch, tmp_path):
    from ngbse20.collectors import http_web
    monkeypatch.setattr(http_web.requests, 'get', fake_get)

    seeds = [{"id": "s1", "query": "https://example.com", "type": "web"}]
    rules = []
    config = {"output_dir": str(tmp_path), "allowlist": ["example.com"]}

    result = run_pipeline(seeds=seeds, rules=rules, config=config)

    assert result["status"] == "ok"
    assert len(result["findings"]) == 1
    assert result["findings"][0]["asset"] == "example.com"
    assert result["forecast"] is not None
    assert result["next_seeds"] is not None

    history_files = list((tmp_path / "history").glob("*.asset_scores.json"))
    assert len(history_files) == 1
