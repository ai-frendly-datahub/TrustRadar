# TRUSTRADAR

기업 신뢰도, 평판, 소비자 만족도 정보를 수집하고 기업별 신뢰도 트렌드를 분석합니다.

## STRUCTURE

```
TrustRadar/
├── trustradar/
│   ├── collector.py              # collect_sources() — 신뢰도 평가 기관, 소비자 리뷰 플랫폼
│   ├── analyzer.py               # apply_entity_rules() — 산업별 키워드 매칭 (금융, 전자상거래, 통신 등)
│   ├── reporter.py               # generate_report() — Jinja2 HTML
│   ├── storage.py                # RadarStorage — DuckDB upsert/query/retention
│   ├── models.py                 # Source, Article, EntityDefinition, CategoryConfig
│   ├── config_loader.py          # YAML 로딩
│   ├── logger.py                 # structlog 구조화 로깅
│   ├── notifier.py               # Email/Webhook 알림
│   ├── raw_logger.py             # JSONL 원시 로깅
│   ├── search_index.py           # SQLite FTS5 전문 검색
│   ├── nl_query.py               # 자연어 쿼리 파서
│   ├── common/                   # 공유 유틸리티
│   └── mcp_server/               # MCP 서버 (server.py + tools.py)
├── config/
│   ├── config.yaml               # database_path, report_dir, raw_data_dir, search_db_path
│   └── categories/trust.yaml  # 소스 + 엔티티 정의
├── data/                         # DuckDB, search_index.db, raw/ JSONL
├── reports/                      # 생성된 HTML 리포트
├── tests/unit/                   # pytest 단위 테스트
├── main.py                       # CLI 엔트리포인트
└── .github/workflows/radar-crawler.yml
```

## ENTITIES

| Entity | Examples |
|--------|----------|
| Vulnerability | CVE, exploit, zero-day, 취약점 |
| DataBreach | data breach, leaked, ransomware |
| Malware | malware, trojan, botnet, 악성코드 |
| Compliance | GDPR, CCPA, FTC, 규정 준수 |

## DEVIATIONS FROM TEMPLATE

- 보안 사고, 개인정보, 위협 인텔리전스, 규제 준수 source를 분리해 추적한다.
- CVE/KEV feed와 보안 뉴스는 incident evidence와 editorial context를 구분한다.
- Reddit 등 cloud IP 차단 source는 CI 수집 대상에서 제외 상태를 유지한다.

## COMMANDS

```bash
python main.py --category trust --recent-days 7
python main.py --category trust --per-source-limit 50 --keep-days 90
```
