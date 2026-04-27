from __future__ import annotations

from datetime import UTC, datetime

from trustradar.models import Article
from trustradar.trust_signals import (
    classify_trust_events,
    enrich_trust_operational_fields,
    extract_affected_services,
    extract_ai_asset_risks,
    extract_enforcement_outcomes,
    extract_incident_status,
    infer_verification_state,
)


def test_extract_incident_status_maps_disclosure_and_resolution_terms() -> None:
    statuses = extract_incident_status(
        "The company disclosed a breach notice and said service was restored."
    )

    assert statuses == ["resolved", "disclosed"]


def test_extract_enforcement_outcomes_maps_penalty_and_remediation() -> None:
    outcomes = extract_enforcement_outcomes(
        "The FTC announced a consent order, penalty, and remediation plan."
    )

    assert outcomes == ["penalty", "settlement", "remediation"]


def test_extract_ai_asset_risks_maps_ai_operational_assets() -> None:
    assets = extract_ai_asset_risks("Prompt log and RAG embeddings were exposed.")

    assert assets == ["rag_embedding", "inference_log"]


def test_extract_ai_asset_risks_does_not_match_rag_inside_words() -> None:
    assets = extract_ai_asset_risks("Attackers leveraged an RCE flaw in a service.")

    assert assets == []


def test_extract_affected_services_normalizes_vendor_aliases() -> None:
    services = extract_affected_services(
        "GitHub Actions outage and Microsoft Azure degraded performance"
    )

    assert services == ["github", "microsoft_azure"]


def test_classify_trust_events_detects_status_complaint_and_ai_asset() -> None:
    events = classify_trust_events(
        "A status page outage affected users while a consumer complaint mentioned leaked prompt logs."
    )

    assert events == [
        "incident_disclosure",
        "status_page_incident",
        "consumer_complaint",
        "ai_asset_risk",
    ]


def test_infer_verification_state_distinguishes_official_and_community_sources() -> None:
    assert infer_verification_state("KISA 보안공지", ["incident_disclosure"]) == "official_confirmed"
    assert (
        infer_verification_state("Lobsters Security Community", ["incident_disclosure"])
        == "official_confirmation_required"
    )


def test_enrich_trust_operational_fields_adds_matched_entities() -> None:
    article = Article(
        title="GitHub breach notice after service outage",
        link="https://example.com/trust",
        summary="The GitHub status page outage was resolved after a consent order and fine.",
        published=datetime(2026, 4, 12, tzinfo=UTC),
        source="Hacker News Security Community",
        category="trust",
        matched_entities={"DataBreach": ["breach"]},
    )

    enriched = enrich_trust_operational_fields([article])[0]

    assert enriched.matched_entities["IncidentStatus"] == ["resolved", "disclosed", "outage"]
    assert enriched.matched_entities["EnforcementOutcome"] == ["penalty", "settlement"]
    assert enriched.matched_entities["ServiceId"] == ["github"]
    assert enriched.matched_entities["AffectedService"] == ["GitHub"]
    assert enriched.matched_entities["OperationalEvent"] == [
        "incident_disclosure",
        "status_page_incident",
        "enforcement_action",
    ]
    assert enriched.matched_entities["VerificationState"] == ["official_confirmation_required"]
