"""Lightweight incident category classifier.

Maps a free-text title + summary to a coarse ``incident_category`` enum so
downstream dashboards can group articles by attack type without ML
infrastructure.

Categories:

- ``BREACH``      : data breach / leak / credential dump
- ``RANSOMWARE``  : ransomware / wiper / cryptolocker
- ``DDOS``        : denial-of-service / volumetric attack
- ``PHISHING``    : phishing / smishing / vishing / credential stuffing
- ``MALWARE``     : trojan / backdoor / spyware / RAT (non-ransom)
- ``VULNERABILITY``: CVE / zero-day / RCE / SQLi / XSS disclosures
- ``REGULATORY`` : fine, settlement, consent decree, GDPR/CCPA action
- ``OTHER``      : matched no category (default)

The classifier returns ``OTHER`` when no keyword fires so dashboards can
filter the matched-vs-unmatched fraction.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

# Order matters: earlier categories win ties.
_CATEGORY_KEYWORDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "RANSOMWARE",
        (
            "ransomware",
            "ransom",
            "랜섬웨어",
            "cryptolocker",
            "lockbit",
            "ryuk",
            "wiper",
            "double extortion",
            "encryptor",
            "암호화 공격",
        ),
    ),
    (
        "DDOS",
        (
            "ddos",
            "denial of service",
            "denial-of-service",
            "분산서비스거부",
            "디도스",
            "udp flood",
            "syn flood",
            "amplification attack",
        ),
    ),
    (
        "PHISHING",
        (
            "phishing",
            "phish",
            "spear-phishing",
            "smishing",
            "vishing",
            "credential stuffing",
            "사기 이메일",
            "피싱",
            "스미싱",
            "비싱",
        ),
    ),
    (
        "BREACH",
        (
            "data breach",
            "data leak",
            "leaked database",
            "leaked data",
            "exposed records",
            "credential dump",
            "정보 유출",
            "개인정보 유출",
            "유출 사고",
            "도난",
            "exfiltrated",
        ),
    ),
    (
        "VULNERABILITY",
        (
            "cve-",
            "zero-day",
            "0-day",
            "0day",
            "remote code execution",
            "rce",
            "sql injection",
            "sqli",
            "cross-site scripting",
            "xss",
            "buffer overflow",
            "취약점",
            "보안 패치",
            "patch tuesday",
        ),
    ),
    (
        "MALWARE",
        (
            "malware",
            "trojan",
            "backdoor",
            "rootkit",
            "spyware",
            "remote access trojan",
            "rat ",
            " rat,",
            "botnet",
            "cryptojacker",
            "악성코드",
            "악성 프로그램",
        ),
    ),
    (
        "REGULATORY",
        (
            "fine",
            "settlement",
            "consent decree",
            "consent order",
            "gdpr",
            "ccpa",
            "data protection authority",
            "icо",
            "과징금",
            "행정처분",
            "시정명령",
        ),
    ),
)


@dataclass(frozen=True)
class IncidentLabel:
    category: str
    matched_keyword: str


def classify_incident(text: str | None) -> IncidentLabel:
    """Return the best-effort incident category for ``text``.

    ``text`` should already be the concatenation of title + summary; the
    function lower-cases for matching but preserves the original keyword
    in the returned label for traceability.
    """
    if not text:
        return IncidentLabel("OTHER", "")
    haystack = text.lower()
    for category, keywords in _CATEGORY_KEYWORDS:
        for keyword in keywords:
            if keyword in haystack:
                return IncidentLabel(category, keyword)
    return IncidentLabel("OTHER", "")


def classify_articles(articles: Iterable[object]) -> dict[str, int]:
    """Iterate over articles (objects with .title and .summary attributes)
    and return a histogram of incident categories."""
    counts: dict[str, int] = {}
    for article in articles:
        title = getattr(article, "title", "") or ""
        summary = getattr(article, "summary", "") or ""
        label = classify_incident(f"{title}\n{summary}")
        counts[label.category] = counts.get(label.category, 0) + 1
    return counts


__all__ = ["IncidentLabel", "classify_incident", "classify_articles"]
