from __future__ import annotations

from importlib import import_module


def test_collect_browser_sources_forwards_source_config(monkeypatch) -> None:
    module = import_module("trustradar.browser_collector")
    source = import_module("trustradar.models").Source(
        name="FTC Press Releases",
        type="javascript",
        url="https://www.ftc.gov/news-events/news/press-releases",
        config={"wait_for": "main"},
    )
    captured: dict[str, object] = {}

    def fake_collect(*, sources, category, timeout, health_db_path):
        captured["sources"] = sources
        captured["category"] = category
        return [], []

    monkeypatch.setattr(module, "_BROWSER_COLLECTION_AVAILABLE", True)
    monkeypatch.setattr(module, "_core_collect", fake_collect)

    articles, errors = module.collect_browser_sources([source], "trust")

    assert articles == []
    assert errors == []
    assert captured["category"] == "trust"
    assert captured["sources"] == [
        {
            "name": "FTC Press Releases",
            "type": "javascript",
            "url": "https://www.ftc.gov/news-events/news/press-releases",
            "config": {"wait_for": "main"},
        }
    ]
