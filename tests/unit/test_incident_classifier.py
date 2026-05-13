from __future__ import annotations

from dataclasses import dataclass

import pytest

from trustradar.incident_classifier import (
    classify_articles,
    classify_incident,
)


@pytest.mark.parametrize(
    "text, expected",
    [
        ("LockBit ransomware hit hospital", "RANSOMWARE"),
        ("Massive DDoS attack on bank", "DDOS"),
        ("Phishing campaign targets HR teams", "PHISHING"),
        ("Data breach exposes 2M users", "BREACH"),
        ("Critical CVE-2026-0001 RCE in OpenSSL", "VULNERABILITY"),
        ("Trojan distributed via fake invoice", "MALWARE"),
        ("Company fined €20M under GDPR", "REGULATORY"),
        ("Quarterly results miss expectations", "OTHER"),
        ("랜섬웨어 공격으로 병원 마비", "RANSOMWARE"),
        ("개인정보 유출 사고 발생", "BREACH"),
        ("취약점 패치 긴급 권고", "VULNERABILITY"),
        ("", "OTHER"),
        (None, "OTHER"),
    ],
)
def test_classify_incident_categories(text, expected) -> None:
    assert classify_incident(text).category == expected


def test_classify_incident_returns_matched_keyword() -> None:
    label = classify_incident("LockBit ransomware hit hospital")
    assert label.matched_keyword in {"ransomware", "lockbit"}


@dataclass
class _FakeArticle:
    title: str
    summary: str


def test_classify_articles_histogram() -> None:
    articles = [
        _FakeArticle("Ransomware in hospital", "LockBit demands"),
        _FakeArticle("CVE-2026-0042 disclosed", "RCE in OpenSSL"),
        _FakeArticle("Quarterly results", "No incidents"),
        _FakeArticle("Phishing campaign", "vishing too"),
    ]
    hist = classify_articles(articles)
    assert hist["RANSOMWARE"] == 1
    assert hist["VULNERABILITY"] == 1
    assert hist["PHISHING"] == 1
    assert hist["OTHER"] == 1
