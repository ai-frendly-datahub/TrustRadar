from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from trustradar.models import Article, CategoryConfig, EntityDefinition, Source
from trustradar.storage import RadarStorage


@pytest.fixture
def tmp_storage(tmp_path: Path) -> RadarStorage:
    """Create a temporary RadarStorage instance for testing."""
    db_path = tmp_path / "test.duckdb"
    storage = RadarStorage(db_path)
    yield storage
    storage.close()


@pytest.fixture
def sample_articles() -> list[Article]:
    """Create sample articles with realistic 신뢰도 domain data."""
    now = datetime.now(timezone.utc)
    return [
        Article(
            title="기업 신뢰도 평가 결과",
            link="https://trust.example.com/rating-2024",
            summary="주요 기업들의 신뢰도 평가 결과입니다.",
            published=now,
            source="trustradar_api",
            category="trust",
            matched_entities={},
        ),
        Article(
            title="소비자 만족도 조사",
            link="https://trust.example.com/satisfaction-2024",
            summary="소비자 만족도 조사 결과를 발표합니다.",
            published=now,
            source="trustradar_api",
            category="trust",
            matched_entities={},
        ),
        Article(
            title="사기 피해 예방 정보",
            link="https://trust.example.com/fraud-2024",
            summary="온라인 사기 피해 예방 방법입니다.",
            published=now,
            source="trustradar_api",
            category="trust",
            matched_entities={},
        ),
        Article(
            title="기업 평판 분석",
            link="https://trust.example.com/reputation-2024",
            summary="기업 평판 분석 결과입니다.",
            published=now,
            source="trustradar_api",
            category="trust",
            matched_entities={},
        ),
        Article(
            title="소비자보호 뉴스",
            link="https://trust.example.com/consumer-2024",
            summary="소비자보호 관련 뉴스입니다.",
            published=now,
            source="trustradar_api",
            category="trust",
            matched_entities={},
        ),
    ]


@pytest.fixture
def sample_entities() -> list[EntityDefinition]:
    """Create sample entities with 신뢰도 domain keywords."""
    return [
        EntityDefinition(
            name="trust_score",
            display_name="신뢰도",
            keywords=["신뢰", "신뢰도", "평가", "점수"],
        ),
        EntityDefinition(
            name="fraud_prevention",
            display_name="사기 예방",
            keywords=["사기", "피해", "예방", "보호"],
        ),
        EntityDefinition(
            name="consumer_protection",
            display_name="소비자보호",
            keywords=["소비자", "보호", "권리", "피해"],
        ),
        EntityDefinition(
            name="reputation",
            display_name="평판",
            keywords=["평판", "이미지", "평가", "리뷰"],
        ),
        EntityDefinition(
            name="satisfaction",
            display_name="만족도",
            keywords=["만족", "만족도", "조사", "평가"],
        ),
    ]


@pytest.fixture
def sample_config(tmp_path: Path, sample_entities: list[EntityDefinition]) -> CategoryConfig:
    """Create a sample CategoryConfig for testing."""
    sources = [
        Source(
            name="trustradar_api",
            type="api",
            url="https://api.trustradar.example.com",
        ),
    ]
    return CategoryConfig(
        category_name="trust",
        display_name="신뢰도",
        sources=sources,
        entities=sample_entities,
    )
