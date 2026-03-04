from __future__ import annotations

import json
from datetime import datetime, timedelta
from importlib import import_module
from pathlib import Path
from typing import Protocol, cast

import duckdb


class _SearchIndex(Protocol):
    def upsert(self, link: str, title: str, body: str) -> None: ...

    def __enter__(self) -> "_SearchIndex": ...

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None: ...


class _SearchIndexCtor(Protocol):
    def __call__(self, db_path: Path) -> _SearchIndex: ...


SearchIndex = cast(_SearchIndexCtor, import_module("trustradar.search_index").SearchIndex)


class _HandleSearch(Protocol):
    def __call__(self, *, search_db_path: Path, db_path: Path, query: str, limit: int = 20) -> str: ...


class _HandleRecentUpdates(Protocol):
    def __call__(self, *, db_path: Path, days: int = 7, limit: int = 20) -> str: ...


class _HandleSql(Protocol):
    def __call__(self, *, db_path: Path, query: str) -> str: ...


class _HandleTopTrends(Protocol):
    def __call__(self, *, db_path: Path, days: int = 7, limit: int = 10) -> str: ...


class _HandleTrustScore(Protocol):
    def __call__(self, *, db_path: Path, days: int = 30, limit: int = 10) -> str: ...


def _load_tools() -> object:
    return import_module("trustradar.mcp_server.tools")


def _init_articles_table(db_path: Path) -> None:
    conn = duckdb.connect(str(db_path))
    try:
        _ = conn.execute(
            """
            CREATE TABLE articles (
                id BIGINT PRIMARY KEY,
                category TEXT NOT NULL,
                source TEXT NOT NULL,
                title TEXT NOT NULL,
                link TEXT NOT NULL UNIQUE,
                summary TEXT,
                published TIMESTAMP,
                collected_at TIMESTAMP NOT NULL,
                entities_json TEXT
            )
            """
        )
    finally:
        conn.close()


def _seed_article(
    *,
    db_path: Path,
    article_id: int,
    title: str,
    link: str,
    collected_at: datetime,
    entities: dict[str, list[str]] | None = None,
) -> None:
    conn = duckdb.connect(str(db_path))
    try:
        _ = conn.execute(
            """
            INSERT INTO articles (id, category, source, title, link, summary, published, collected_at, entities_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                article_id,
                "trust",
                "Test Source",
                title,
                link,
                "summary",
                None,
                collected_at,
                json.dumps(entities or {}, ensure_ascii=False),
            ],
        )
    finally:
        conn.close()


def test_handle_search(tmp_path: Path) -> None:
    tools = _load_tools()
    handle_search = cast(_HandleSearch, getattr(tools, "handle_search"))

    db_path = tmp_path / "trustradar.duckdb"
    search_db_path = tmp_path / "search.db"
    _init_articles_table(db_path)

    now = datetime.now()
    recent_link = "https://example.com/recent"
    old_link = "https://example.com/old"

    _seed_article(
        db_path=db_path,
        article_id=1,
        title="Recent trustpilot review trend",
        link=recent_link,
        collected_at=now - timedelta(days=2),
    )
    _seed_article(
        db_path=db_path,
        article_id=2,
        title="Old fake review issue",
        link=old_link,
        collected_at=now - timedelta(days=20),
    )

    with SearchIndex(search_db_path) as idx:
        idx.upsert(recent_link, "Recent trustpilot review trend", "Trustpilot rating improved")
        idx.upsert(old_link, "Old fake review issue", "Review fraud concern")

    output = handle_search(
        search_db_path=search_db_path,
        db_path=db_path,
        query="last 7 days trustpilot",
        limit=10,
    )

    assert "Recent trustpilot review trend" in output
    assert "Old fake review issue" not in output


def test_handle_recent_updates(tmp_path: Path) -> None:
    tools = _load_tools()
    handle_recent_updates = cast(_HandleRecentUpdates, getattr(tools, "handle_recent_updates"))

    db_path = tmp_path / "trustradar.duckdb"
    _init_articles_table(db_path)
    now = datetime.now()

    _seed_article(
        db_path=db_path,
        article_id=1,
        title="Most recent",
        link="https://example.com/1",
        collected_at=now - timedelta(hours=1),
    )
    _seed_article(
        db_path=db_path,
        article_id=2,
        title="Older",
        link="https://example.com/2",
        collected_at=now - timedelta(days=2),
    )

    output = handle_recent_updates(db_path=db_path, days=1, limit=10)

    assert "Most recent" in output
    assert "Older" not in output


def test_handle_sql_select(tmp_path: Path) -> None:
    tools = _load_tools()
    handle_sql = cast(_HandleSql, getattr(tools, "handle_sql"))

    db_path = tmp_path / "trustradar.duckdb"
    _init_articles_table(db_path)

    output = handle_sql(db_path=db_path, query="SELECT COUNT(*) AS total FROM articles")

    assert "total" in output
    assert "0" in output


def test_handle_sql_blocked(tmp_path: Path) -> None:
    tools = _load_tools()
    handle_sql = cast(_HandleSql, getattr(tools, "handle_sql"))

    db_path = tmp_path / "trustradar.duckdb"
    _init_articles_table(db_path)

    output = handle_sql(db_path=db_path, query="DROP TABLE articles")

    assert "Only SELECT/WITH/EXPLAIN queries are allowed" in output


def test_handle_top_trends(tmp_path: Path) -> None:
    tools = _load_tools()
    handle_top_trends = cast(_HandleTopTrends, getattr(tools, "handle_top_trends"))

    db_path = tmp_path / "trustradar.duckdb"
    _init_articles_table(db_path)
    now = datetime.now()

    _seed_article(
        db_path=db_path,
        article_id=1,
        title="a",
        link="https://example.com/a",
        collected_at=now - timedelta(days=1),
        entities={"ReviewQuality": ["fake review", "fraud"], "Platform": ["trustpilot"]},
    )
    _seed_article(
        db_path=db_path,
        article_id=2,
        title="b",
        link="https://example.com/b",
        collected_at=now - timedelta(days=1),
        entities={"Reputation": ["reputation"]},
    )

    output = handle_top_trends(db_path=db_path, days=7, limit=10)

    assert "ReviewQuality" in output
    assert "2" in output
    assert "Platform" in output
    assert "1" in output


def test_handle_trust_score(tmp_path: Path) -> None:
    tools = _load_tools()
    handle_trust_score = cast(_HandleTrustScore, getattr(tools, "handle_trust_score"))

    db_path = tmp_path / "trustradar.duckdb"
    _init_articles_table(db_path)
    now = datetime.now()

    _seed_article(
        db_path=db_path,
        article_id=1,
        title="Positive trust signals",
        link="https://example.com/positive",
        collected_at=now - timedelta(days=1),
        entities={"Rating": ["rating", "평점"], "Platform": ["trustpilot"]},
    )
    _seed_article(
        db_path=db_path,
        article_id=2,
        title="Negative trust signals",
        link="https://example.com/negative",
        collected_at=now - timedelta(days=1),
        entities={"Complaint": ["complaint", "bad review"], "ReviewQuality": ["fake review"]},
    )

    output = handle_trust_score(db_path=db_path, days=7, limit=10)

    assert "Trust score analysis (last 7 days):" in output
    assert "Overall trust score:" in output
    assert "positive: 3" in output
    assert "negative: 3" in output
    assert "Rating: 2" in output
    assert "Complaint: 2" in output


def test_handle_trust_score_no_data(tmp_path: Path) -> None:
    tools = _load_tools()
    handle_trust_score = cast(_HandleTrustScore, getattr(tools, "handle_trust_score"))

    db_path = tmp_path / "trustradar.duckdb"
    _init_articles_table(db_path)

    output = handle_trust_score(db_path=db_path, days=7, limit=5)

    assert output == "No trust score data available."
