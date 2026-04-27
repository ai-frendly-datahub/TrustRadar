from __future__ import annotations

from trustradar.config_loader import load_category_config, load_category_quality_config


def test_real_trust_config_exposes_data_quality_overlay() -> None:
    metadata = load_category_quality_config("trust")

    data_quality = metadata["data_quality"]
    assert isinstance(data_quality, dict)
    assert data_quality["priority"] == "P0"
    assert data_quality["primary_motion"] == "compliance-risk"
    assert "incident_disclosure" in data_quality["event_models"]
    assert "status_page_incident" in data_quality["event_models"]
    assert "ai_asset_risk" in data_quality["event_models"]
    assert data_quality["canonical_keys"]["incident"]["fields"]
    quality_outputs = data_quality["quality_outputs"]
    assert quality_outputs["freshness_report"] == "reports/trust_quality.json"
    assert quality_outputs["dated_freshness_report_pattern"] == (
        "reports/trust_YYYYMMDD_quality.json"
    )
    assert set(quality_outputs["tracked_event_models"]) >= {
        "incident_disclosure",
        "status_page_incident",
        "enforcement_action",
        "consumer_complaint",
        "ai_asset_risk",
    }

    backlog = metadata["source_backlog"]
    assert isinstance(backlog, dict)
    status_candidates = {candidate["id"] for candidate in backlog["status_page_candidates"]}
    disclosure_candidates = {
        candidate["id"] for candidate in backlog["incident_disclosure_candidates"]
    }
    assert status_candidates >= {"official_status_pages", "statuspage_io_incident_feeds"}
    assert disclosure_candidates >= {"state_attorney_general_breach_notices", "hhs_ocr_breach_portal"}


def test_real_trust_sources_preserve_operational_metadata() -> None:
    config = load_category_config("trust")
    sources = {source.name: source for source in config.sources}

    kisa = sources["KISA 보안공지"]
    assert kisa.trust_tier == "T1_official"
    assert kisa.config["event_model"] == "incident_disclosure"
    assert kisa.config["verification_role"] == "official_disclosure"

    pipc = sources["PIPC 개인정보보호위원회"]
    assert pipc.config["event_model"] == "enforcement_action"
    assert pipc.config["merge_policy"] == "authoritative_source"

    hnews = sources["Hacker News Security Community"]
    assert hnews.trust_tier == "T4_community"
    assert hnews.config["merge_policy"] == "requires_official_confirmation"

    sans = sources["SANS Internet Storm Center"]
    assert "include_keywords" in sans.config

    lobsters = sources["Lobsters Security Community"]
    assert "LLM" in lobsters.config["include_keywords"]

    stack_exchange = sources["Information Security Stack Exchange"]
    assert stack_exchange.config["verification_role"] == "community_signal"

    ai_asset_risk = next(entity for entity in config.entities if entity.name == "AIAssetRisk")
    assert "LLM" in ai_asset_risk.keywords
    assert "cargo-crev" in ai_asset_risk.keywords


def test_load_category_config_preserves_source_metadata(tmp_path) -> None:
    categories_dir = tmp_path / "categories"
    categories_dir.mkdir()
    (categories_dir / "trust.yaml").write_text(
        """
category_name: trust
display_name: Trust
sources:
  - name: FTC Press Releases
    id: ftc_press
    type: javascript
    url: https://www.ftc.gov/news-events/news/press-releases
    enabled: false
    trust_tier: T1_official
    weight: 1.5
    content_type: notice
    collection_tier: C3_html_js
    producer_role: government
    info_purpose:
      - enforcement
      - complaint
    notes: official privacy enforcement feed
    config:
      wait_for: main
entities: []
""",
        encoding="utf-8",
    )

    config = load_category_config("trust", categories_dir=categories_dir)
    source = config.sources[0]

    assert source.id == "ftc_press"
    assert source.enabled is False
    assert source.trust_tier == "T1_official"
    assert source.weight == 1.5
    assert source.content_type == "notice"
    assert source.collection_tier == "C3_html_js"
    assert source.producer_role == "government"
    assert source.info_purpose == ["enforcement", "complaint"]
    assert source.notes == "official privacy enforcement feed"
    assert source.config == {"wait_for": "main"}
