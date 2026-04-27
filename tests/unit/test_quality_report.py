from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

from trustradar.models import Article, CategoryConfig, Source
from trustradar.quality_report import build_quality_report, write_quality_report


def _source(
    name: str,
    event_model: str,
    sla_days: int | None = None,
    *,
    enabled: bool = True,
    verification_role: str = "",
    merge_policy: str = "",
    disabled_reason: str = "",
    required_before_enable: list[str] | None = None,
) -> Source:
    config: dict[str, object] = {"event_model": event_model}
    if sla_days is not None:
        config["freshness_sla_days"] = sla_days
    if verification_role:
        config["verification_role"] = verification_role
    if merge_policy:
        config["merge_policy"] = merge_policy
    if disabled_reason:
        config["disabled_reason"] = disabled_reason
    if required_before_enable:
        config["required_before_enable"] = required_before_enable
    return Source(
        name=name,
        type="rss",
        url=f"https://example.com/{name}",
        enabled=enabled,
        config=config,
    )


def test_build_quality_report_tracks_trust_verification_statuses() -> None:
    now = datetime(2026, 4, 12, tzinfo=UTC)
    category = CategoryConfig(
        category_name="trust",
        display_name="Trust",
        sources=[
            _source(
                "Official Disclosure",
                "incident_disclosure",
                1,
                verification_role="official_disclosure",
                merge_policy="authoritative_source",
            ),
            _source(
                "Community Source",
                "incident_disclosure",
                1,
                verification_role="community_signal",
                merge_policy="requires_official_confirmation",
            ),
            _source("Missing Status", "status_page_incident", 1),
            _source(
                "Enforcement Source",
                "enforcement_action",
                1,
                verification_role="official_action",
                merge_policy="authoritative_source",
            ),
            _source(
                "AI Guidance",
                "ai_asset_risk",
                7,
                verification_role="official_guidance",
                merge_policy="authoritative_source",
            ),
            _source("General News", "market_context", 7),
        ],
        entities=[],
    )
    articles = [
        Article(
            title="Official breach notice",
            link="https://example.com/official",
            summary="The breach notice disclosed an incident.",
            published=now - timedelta(hours=6),
            collected_at=now,
            source="Official Disclosure",
            category="trust",
            matched_entities={
                "IncidentStatus": ["disclosed"],
                "OperationalEvent": ["incident_disclosure"],
                "VerificationState": ["official_confirmed"],
            },
        ),
        Article(
            title="Community reports an outage",
            link="https://example.com/community",
            summary="A status page outage is under discussion.",
            published=now - timedelta(hours=3),
            collected_at=now,
            source="Community Source",
            category="trust",
            matched_entities={
                "IncidentStatus": ["outage"],
                "ServiceId": ["github"],
                "AffectedService": ["GitHub"],
                "OperationalEvent": ["status_page_incident"],
                "VerificationState": ["official_confirmation_required"],
            },
        ),
        Article(
            title="Privacy regulator consent order",
            link="https://example.com/enforcement",
            summary="The regulator announced a penalty and remediation.",
            published=now - timedelta(days=3),
            collected_at=now,
            source="Enforcement Source",
            category="trust",
            matched_entities={
                "EnforcementOutcome": ["penalty", "remediation"],
                "OperationalEvent": ["enforcement_action"],
                "VerificationState": ["official_confirmed"],
            },
        ),
        Article(
            title="AI security guidance",
            link="https://example.com/ai",
            summary="Guidance covers prompt logs and embeddings.",
            published=now - timedelta(days=1),
            collected_at=now,
            source="AI Guidance",
            category="trust",
            matched_entities={
                "AIAssetRisk": ["rag_embedding", "inference_log"],
                "OperationalEvent": ["ai_asset_risk"],
                "VerificationState": ["official_confirmed"],
            },
        ),
        Article(
            title="General trust coverage",
            link="https://example.com/general",
            summary="Context without an operational event.",
            published=now,
            collected_at=now,
            source="General News",
            category="trust",
        ),
    ]

    report = build_quality_report(
        category=category,
        articles=articles,
        errors=["Enforcement Source: timeout after retry"],
        quality_config={
            "data_quality": {
                "quality_outputs": {
                    "tracked_event_models": [
                        "incident_disclosure",
                        "status_page_incident",
                        "enforcement_action",
                        "consumer_complaint",
                        "ai_asset_risk",
                    ]
                }
            }
        },
        generated_at=now,
    )

    assert report["summary"]["fresh_sources"] == 3
    assert report["summary"]["stale_sources"] == 1
    assert report["summary"]["missing_sources"] == 1
    assert report["summary"]["not_tracked_sources"] == 1
    assert report["summary"]["incident_disclosure_events"] == 2
    assert report["summary"]["status_page_incident_events"] == 1
    assert report["summary"]["enforcement_action_events"] == 1
    assert report["summary"]["consumer_complaint_events"] == 0
    assert report["summary"]["ai_asset_risk_events"] == 1
    assert report["summary"]["official_confirmed_events"] == 3
    assert report["summary"]["official_confirmation_required_events"] == 2
    assert report["summary"]["unique_service_count"] == 1
    assert report["summary"]["official_confirmation_required_service_count"] == 1
    assert report["summary"]["collection_error_count"] == 1
    assert "official_confirmation_required" in report["verification_scope_note"]

    statuses = {row["source"]: row["status"] for row in report["sources"]}
    assert statuses == {
        "Official Disclosure": "fresh",
        "Community Source": "fresh",
        "Missing Status": "missing",
        "Enforcement Source": "stale",
        "AI Guidance": "fresh",
        "General News": "not_tracked",
    }
    community_events = [
        row for row in report["events"] if row["source"] == "Community Source"
    ]
    assert {row["event_model"] for row in community_events} == {
        "incident_disclosure",
        "status_page_incident",
    }
    assert {row["verification_state"] for row in community_events} == {
        "official_confirmation_required"
    }
    assert {row["service_key"] for row in community_events} == {"github"}
    assert {tuple(row["affected_services"]) for row in community_events} == {("GitHub",)}
    enforcement_event = next(
        row for row in report["events"] if row["event_model"] == "enforcement_action"
    )
    assert enforcement_event["enforcement_outcomes"] == ["penalty", "remediation"]


def test_write_quality_report_writes_latest_and_dated_files(tmp_path) -> None:
    report = {
        "category": "trust",
        "generated_at": "2026-04-12T03:04:05+00:00",
        "verification_scope_note": "note",
        "summary": {},
        "sources": [],
        "events": [],
        "errors": [],
    }

    paths = write_quality_report(report, output_dir=tmp_path, category_name="trust")

    assert paths["latest"] == tmp_path / "trust_quality.json"
    assert paths["dated"] == tmp_path / "trust_20260412_quality.json"
    assert json.loads(paths["latest"].read_text(encoding="utf-8")) == report
    assert json.loads(paths["dated"].read_text(encoding="utf-8")) == report


def test_build_quality_report_excludes_disabled_sources_from_active_tracking() -> None:
    now = datetime(2026, 4, 12, tzinfo=UTC)
    category = CategoryConfig(
        category_name="trust",
        display_name="Trust",
        sources=[
            _source("Enabled Official", "enforcement_action", 1),
            _source(
                "Disabled Official",
                "enforcement_action",
                1,
                enabled=False,
                disabled_reason="blocked_by_source",
                required_before_enable=["parser_smoke"],
            ),
        ],
        entities=[],
    )
    articles = [
        Article(
            title="Enabled enforcement",
            link="https://example.com/enabled",
            summary="The regulator announced a consent order.",
            published=now,
            collected_at=now,
            source="Enabled Official",
            category="trust",
            matched_entities={"OperationalEvent": ["enforcement_action"]},
        ),
        Article(
            title="Disabled enforcement",
            link="https://example.com/disabled",
            summary="This row came from an older run before the source was disabled.",
            published=now,
            collected_at=now,
            source="Disabled Official",
            category="trust",
            matched_entities={"OperationalEvent": ["enforcement_action"]},
        ),
    ]

    report = build_quality_report(
        category=category,
        articles=articles,
        quality_config={},
        generated_at=now,
    )

    assert report["summary"]["tracked_sources"] == 1
    assert report["summary"]["fresh_sources"] == 1
    assert report["summary"]["skipped_disabled_sources"] == 1
    assert report["summary"]["enforcement_action_events"] == 1

    disabled_row = next(row for row in report["sources"] if row["source"] == "Disabled Official")
    assert disabled_row["enabled"] is False
    assert disabled_row["tracked"] is False
    assert disabled_row["status"] == "skipped_disabled"
    assert disabled_row["disabled_reason"] == "blocked_by_source"
    assert disabled_row["required_before_enable"] == ["parser_smoke"]
    assert all(row["source"] != "Disabled Official" for row in report["events"])
