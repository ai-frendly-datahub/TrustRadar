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


def test_collect_browser_sources_retries_only_failed_sources(monkeypatch) -> None:
    module = import_module("trustradar.browser_collector")
    models = import_module("trustradar.models")
    sources = [
        models.Source(
            name="KISA 보안공지",
            type="javascript",
            url="https://www.kisa.or.kr/401",
            config={"wait_for": "body"},
        ),
        models.Source(
            name="PIPC 개인정보보호위원회",
            type="javascript",
            url="https://www.pipc.go.kr/np/cop/bbs/selectBoardList.do?bbsId=BS074",
            config={"wait_for": "body"},
        ),
    ]
    calls: list[list[str]] = []

    def fake_collect(*, sources, category, timeout, health_db_path):
        calls.append([source["name"] for source in sources])
        if len(calls) == 1:
            return [], ["PIPC 개인정보보호위원회: Page.goto: net::ERR_CONNECTION_RESET"]
        return [
            models.Article(
                title="PIPC enforcement",
                link="https://example.com/pipc",
                summary="PIPC enforcement summary",
                published=None,
                source="PIPC 개인정보보호위원회",
                category=category,
            )
        ], []

    monkeypatch.setattr(module, "_BROWSER_COLLECTION_AVAILABLE", True)
    monkeypatch.setattr(module, "_core_collect", fake_collect)

    articles, errors = module.collect_browser_sources(sources, "trust")

    assert calls == [
        ["KISA 보안공지", "PIPC 개인정보보호위원회"],
        ["PIPC 개인정보보호위원회"],
    ]
    assert errors == []
    assert len(articles) == 1
    assert articles[0].source == "PIPC 개인정보보호위원회"
