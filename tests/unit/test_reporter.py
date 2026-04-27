from __future__ import annotations

from datetime import UTC, datetime

from trustradar.models import Article, CategoryConfig
from trustradar.reporter import generate_report


def test_generate_report_injects_trust_quality_panel(tmp_path, monkeypatch) -> None:
    fixed_now = datetime(2026, 4, 12, 9, 30, tzinfo=UTC)

    class FixedDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            if tz is None:
                return fixed_now.replace(tzinfo=None)
            return fixed_now.astimezone(tz)

    monkeypatch.setattr("radar_core.report_utils.datetime", FixedDateTime)

    output_path = tmp_path / "reports" / "trust_report.html"
    category = CategoryConfig(
        category_name="trust",
        display_name="Trust",
        sources=[],
        entities=[],
    )
    article = Article(
        title="Breach notice after service outage",
        link="https://example.com/trust",
        summary="The outage was resolved after a fine.",
        published=fixed_now,
        collected_at=fixed_now,
        source="KISA 보안공지",
        category="trust",
        matched_entities={"IncidentStatus": ["resolved"]},
    )
    quality_report = {
        "verification_scope_note": (
            "Community and security-media signals are retained as verification evidence."
        ),
        "summary": {
            "fresh_sources": 1,
            "stale_sources": 1,
            "missing_sources": 0,
            "incident_disclosure_events": 1,
            "status_page_incident_events": 1,
            "enforcement_action_events": 1,
            "consumer_complaint_events": 0,
            "ai_asset_risk_events": 1,
            "unique_service_count": 1,
            "official_confirmation_required_events": 1,
        },
        "sources": [
            {
                "source": "Missing Status",
                "status": "stale",
                "event_model": "status_page_incident",
                "age_days": 3,
            }
        ],
        "events": [
            {
                "source": "KISA 보안공지",
                "event_model": "incident_disclosure",
                "title": "Breach notice after service outage",
                "incident_status": ["resolved", "disclosed"],
                "enforcement_outcomes": [],
                "ai_asset_risks": [],
                "verification_state": "official_confirmed",
                "verification_role": "official_disclosure",
            },
            {
                "source": "Hacker News Security Community",
                "event_model": "status_page_incident",
                "title": "Community reports an outage",
                "incident_status": ["outage"],
                "enforcement_outcomes": [],
                "ai_asset_risks": ["inference_log"],
                "affected_services": ["GitHub"],
                "verification_state": "official_confirmation_required",
                "verification_role": "community_signal",
            },
        ],
    }

    generate_report(
        category=category,
        articles=[article],
        output_path=output_path,
        stats={"sources": 1, "collected": 1, "matched": 1, "window_days": 7},
        quality_report=quality_report,
    )

    html = output_path.read_text(encoding="utf-8")
    dated_html = (tmp_path / "reports" / "trust_20260412.html").read_text(
        encoding="utf-8"
    )

    for rendered in (html, dated_html):
        assert 'id="trust-quality"' in rendered
        assert "Trust Quality" in rendered
        assert "trust_quality.json" in rendered
        assert "Missing Status" in rendered
        assert "Breach notice after service outage" in rendered
        assert "service GitHub" in rendered
        assert "official_confirmation_required" in rendered
        assert "community_signal" in rendered
        assert rendered == "\n".join(line.rstrip() for line in rendered.splitlines()) + "\n"

    summary = (tmp_path / "reports" / "trust_20260412_summary.json").read_text(
        encoding="utf-8"
    )
    assert '"repo": "TrustRadar"' in summary
    assert '"ontology_version": "0.1.0"' in summary
    assert '"trust.incident_disclosure"' in summary
