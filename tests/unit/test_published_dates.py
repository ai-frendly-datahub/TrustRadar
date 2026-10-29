"""Published instants stay on the UTC clock when the crawler runs in Asia/Seoul."""

from __future__ import annotations

import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from trustradar.collector import _extract_datetime, _extract_published
from trustradar.models import Article, Source
from trustradar.storage import RadarStorage


_STRUCT = time.struct_time((2026, 10, 28, 15, 0, 0, 2, 301, 0))
_KST = ZoneInfo("Asia/Seoul")


def _use_seoul(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TZ", "Asia/Seoul")
    time.tzset()


def test_feedparser_struct_stores_1500_utc_under_seoul(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _use_seoul(monkeypatch)
    try:
        source = Source(name="example", type="rss", url="https://example.com/feed.xml")
        published = _extract_datetime({"published_parsed": _STRUCT}, source)
        updated = _extract_datetime({"updated_parsed": _STRUCT}, source)
        assert published == datetime(2026, 10, 28, 15, 0, tzinfo=UTC)
        assert updated == published

        storage = RadarStorage(tmp_path / "radar.duckdb")
        try:
            storage.upsert_articles(
                [
                    Article(
                        title="notice",
                        link="https://example.com/a",
                        summary="body",
                        published=published,
                        source=source.name,
                        category="trust",
                    )
                ]
            )
            row = storage.conn.execute("SELECT published FROM articles").fetchone()
            assert row is not None
            stored = row[0]
            assert isinstance(stored, datetime)
            assert stored.replace(tzinfo=UTC) == datetime(2026, 10, 28, 15, 0, tzinfo=UTC)
            loaded = storage.recent_articles("trust", days=3650)
            assert loaded[0].published == datetime(2026, 10, 28, 15, 0, tzinfo=UTC)
        finally:
            storage.close()
    finally:
        monkeypatch.undo()
        time.tzset()


def test_offset_string_is_kept() -> None:
    parsed, raw = _extract_published(
        {"published": "Thu, 29 Oct 2026 09:00:00 +0900"},
        Source(name="example", type="rss", url="https://example.com/feed.xml"),
    )
    assert raw == "Thu, 29 Oct 2026 09:00:00 +0900"
    assert parsed is not None
    assert parsed.utcoffset() == timedelta(hours=9)
    assert parsed.astimezone(UTC) == datetime(2026, 10, 29, 0, 0, tzinfo=UTC)


def test_zoneless_string_uses_source_or_kr_default() -> None:
    kr_struct = time.struct_time((2026, 10, 29, 18, 0, 0, 3, 302, 0))
    kr_parsed, kr_raw = _extract_published(
        {"published": "2026-10-29 18:00:00", "published_parsed": kr_struct},
        Source(name="인벤", type="rss", url="https://www.inven.co.kr/rss/news.xml"),
    )
    assert kr_raw == "2026-10-29 18:00:00"
    assert kr_parsed == datetime(2026, 10, 29, 18, 0, tzinfo=_KST)

    configured, _raw = _extract_published(
        {"published": "2026-10-29 18:00:00"},
        Source(
            name="example",
            type="rss",
            url="https://example.com/feed.xml",
            config={"default_timezone": "Asia/Seoul"},
        ),
    )
    assert configured == datetime(2026, 10, 29, 18, 0, tzinfo=_KST)

    explicit, _explicit_raw = _extract_published(
        {"published": "2026-10-29 18:00:00"},
        Source(
            name="example",
            type="rss",
            url="https://example.com/feed.xml",
            default_timezone="Asia/Seoul",
        ),
    )
    assert explicit == datetime(2026, 10, 29, 18, 0, tzinfo=_KST)
