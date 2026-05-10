from __future__ import annotations

from datetime import UTC, datetime

from main import _quality_lookback_days, _reanalyze_articles
from trustradar.models import Article, CategoryConfig, EntityDefinition, Source


def test_quality_lookback_extends_beyond_report_window_and_sla() -> None:
    source = Source(
        name="Krebs on Security",
        type="rss",
        url="https://krebsonsecurity.com/feed/",
        config={"event_model": "incident_disclosure", "freshness_sla_days": 5},
    )

    lookback_days = _quality_lookback_days(
        {
            "data_quality": {
                "freshness_sla": {
                    "incident_disclosure": {"max_age_days": 1, "stale_after_days": 3},
                    "ai_asset_risk": {"max_age_days": 7, "stale_after_days": 30},
                }
            }
        },
        sources=[source],
        minimum_days=1,
    )

    assert lookback_days == 90


def test_reanalyze_articles_uses_current_entity_rules_for_stored_rows() -> None:
    category = CategoryConfig(
        category_name="trust",
        display_name="Trust",
        sources=[],
        entities=[
            EntityDefinition(
                name="SecurityGeneral",
                display_name="Security",
                keywords=["TLS", "정보보호", "IP카메라"],
            )
        ],
    )
    article = Article(
        title="Microsoft to deprecate legacy TLS in Exchange Online",
        link="https://example.com/tls",
        summary="Existing stored row had no entities before the current rules.",
        published=datetime(2026, 4, 28, tzinfo=UTC),
        source="Bleeping Computer",
        category="trust",
        matched_entities={},
    )

    analyzed = _reanalyze_articles([article], category_cfg=category)

    assert analyzed[0].matched_entities == {"SecurityGeneral": ["tls"]}
