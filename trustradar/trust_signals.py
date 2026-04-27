from __future__ import annotations

import re
from typing import Iterable

from .models import Article


_ASCII_TOKEN_RE = re.compile(r"[0-9a-z]")
_OFFICIAL_SOURCE_MARKERS = (
    "kisa",
    "pipc",
    "ftc",
    "cfpb",
    "circl",
    "ncsc",
)
_COMMUNITY_SOURCE_MARKERS = (
    "hacker news",
    "lobsters",
    "stack exchange",
    "reddit",
)
_MARKET_SOURCE_MARKERS = (
    "bleeping",
    "dark reading",
    "krebs",
    "hacker news",
    "infosecurity",
    "help net",
)
_INCIDENT_MARKERS = (
    "incident disclosure",
    "breach notice",
    "data breach",
    "security incident",
    "unauthorized access",
    "notified affected users",
    "compromised",
    "ransomware",
    "침해사고",
    "유출 통지",
    "개인정보 유출",
)
_STATUS_MARKERS = {
    "investigating": ("investigating", "under investigation", "조사 중", "조사중"),
    "identified": ("identified", "root cause", "원인 파악"),
    "mitigating": ("mitigating", "mitigation", "workaround", "완화"),
    "resolved": ("resolved", "restored", "recovered", "복구", "해결", "정상화"),
    "disclosed": ("disclosed", "breach notice", "notified", "공시", "통지"),
    "outage": ("outage", "downtime", "degraded performance", "service disruption", "장애", "서비스 중단"),
}
_ENFORCEMENT_MARKERS = {
    "penalty": ("penalty", "fine", "civil money penalty", "과징금", "과태료", "벌금"),
    "settlement": ("settlement", "settled", "consent order", "합의", "조정"),
    "corrective_order": ("corrective order", "injunction", "cease and desist", "시정명령", "시정조치"),
    "remediation": ("remediation", "remediate", "corrective action", "개선", "재발방지"),
    "sanction": ("sanction", "enforcement action", "제재", "처분"),
}
_COMPLAINT_MARKERS = (
    "complaint",
    "consumer complaint",
    "deceptive",
    "misleading",
    "scam",
    "fraud",
    "refund",
    "피해구제",
    "민원",
    "분쟁",
    "사기",
    "환불",
)
_AI_ASSET_MARKERS = {
    "model_weights": ("model weights", "model weight", "모델 가중치"),
    "rag_embedding": ("embedding", "embeddings", "rag", "vector database", "임베딩"),
    "inference_log": (
        "inference log",
        "inference logs",
        "prompt log",
        "prompt logs",
        "chat log",
        "chat logs",
        "추론 로그",
        "프롬프트 로그",
    ),
    "training_data": ("training data", "training dataset", "학습 데이터"),
}
_SERVICE_ALIASES: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("github", "GitHub", ("github", "github.com", "github actions", "github copilot")),
    ("cloudflare", "Cloudflare", ("cloudflare",)),
    ("aws", "AWS", ("aws", "amazon web services")),
    ("google_cloud", "Google Cloud", ("google cloud", "gcp")),
    ("microsoft_azure", "Microsoft Azure", ("microsoft azure", "azure")),
    ("microsoft_teams", "Microsoft Teams", ("microsoft teams",)),
    ("okta", "Okta", ("okta",)),
    ("slack", "Slack", ("slack",)),
    ("atlassian", "Atlassian", ("atlassian", "jira", "confluence")),
    ("openai", "OpenAI", ("openai", "chatgpt")),
    ("salesforce", "Salesforce", ("salesforce",)),
    ("crowdstrike", "CrowdStrike", ("crowdstrike",)),
    ("snowflake", "Snowflake", ("snowflake",)),
    ("dropbox", "Dropbox", ("dropbox",)),
)


def _contains_any(text_lower: str, markers: Iterable[str]) -> bool:
    return any(_contains_marker(text_lower, marker) for marker in markers)


def _contains_marker(text_lower: str, marker: str) -> bool:
    normalized = marker.lower().strip()
    if not normalized:
        return False
    if normalized.isascii() and _ASCII_TOKEN_RE.search(normalized):
        pattern = rf"(?<![0-9a-z]){re.escape(normalized)}(?![0-9a-z])"
        return re.search(pattern, text_lower) is not None
    return normalized in text_lower


def extract_incident_status(text: str) -> list[str]:
    text_lower = text.lower()
    return [status for status, markers in _STATUS_MARKERS.items() if _contains_any(text_lower, markers)]


def extract_enforcement_outcomes(text: str) -> list[str]:
    text_lower = text.lower()
    return [outcome for outcome, markers in _ENFORCEMENT_MARKERS.items() if _contains_any(text_lower, markers)]


def extract_ai_asset_risks(text: str) -> list[str]:
    text_lower = text.lower()
    return [asset for asset, markers in _AI_ASSET_MARKERS.items() if _contains_any(text_lower, markers)]


def extract_affected_services(text: str) -> list[str]:
    text_lower = text.lower()
    services: list[str] = []
    for service_id, _display_name, aliases in _SERVICE_ALIASES:
        if _contains_any(text_lower, aliases):
            services.append(service_id)
    return list(dict.fromkeys(services))


def service_display_name(service_id: str) -> str:
    for candidate_id, display_name, _aliases in _SERVICE_ALIASES:
        if candidate_id == service_id:
            return display_name
    return service_id


def classify_trust_events(text: str) -> list[str]:
    text_lower = text.lower()
    statuses = extract_incident_status(text)
    outcomes = extract_enforcement_outcomes(text)
    assets = extract_ai_asset_risks(text)
    events: list[str] = []
    if _contains_any(text_lower, _INCIDENT_MARKERS) or any(status in statuses for status in ("disclosed", "outage")):
        events.append("incident_disclosure")
    if "outage" in statuses:
        events.append("status_page_incident")
    if outcomes:
        events.append("enforcement_action")
    if _contains_any(text_lower, _COMPLAINT_MARKERS):
        events.append("consumer_complaint")
    if assets:
        events.append("ai_asset_risk")
    return list(dict.fromkeys(events))


def infer_verification_state(source_name: str, events: Iterable[str]) -> str:
    source_lower = source_name.lower()
    event_list = list(events)
    if not event_list:
        return "no_operational_event"
    if any(marker in source_lower for marker in _OFFICIAL_SOURCE_MARKERS):
        return "official_confirmed"
    if any(marker in source_lower for marker in _COMMUNITY_SOURCE_MARKERS):
        return "official_confirmation_required"
    if any(marker in source_lower for marker in _MARKET_SOURCE_MARKERS):
        return "corroborating_report_requires_official_source"
    return "verification_required"


def _append_unique(mapping: dict[str, list[str]], key: str, values: Iterable[str]) -> None:
    existing = mapping.setdefault(key, [])
    for value in values:
        if value and value not in existing:
            existing.append(value)


def enrich_trust_operational_fields(articles: Iterable[Article]) -> list[Article]:
    enriched: list[Article] = []
    for article in articles:
        text = f"{article.title} {article.summary}"
        statuses = extract_incident_status(text)
        outcomes = extract_enforcement_outcomes(text)
        assets = extract_ai_asset_risks(text)
        services = extract_affected_services(text)
        events = classify_trust_events(text)
        verification_state = infer_verification_state(article.source, events)

        matched = dict(article.matched_entities)
        if statuses:
            _append_unique(matched, "IncidentStatus", statuses)
        if outcomes:
            _append_unique(matched, "EnforcementOutcome", outcomes)
        if assets:
            _append_unique(matched, "AIAssetRisk", assets)
        if services:
            _append_unique(matched, "ServiceId", services)
            _append_unique(matched, "AffectedService", [service_display_name(service) for service in services])
        if events:
            _append_unique(matched, "OperationalEvent", events)
            _append_unique(matched, "VerificationState", [verification_state])
        article.matched_entities = matched
        enriched.append(article)
    return enriched
