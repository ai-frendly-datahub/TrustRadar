# TRUSTRADAR

보안·개인정보·규제 집행·사고 공시 신호를 수집해 기업 trust/compliance risk를 분석합니다.

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
│   └── categories/{domain}.yaml  # 소스 + 엔티티 정의
├── data/                         # DuckDB, search_index.db, raw/ JSONL
├── reports/                      # 생성된 HTML 리포트
├── tests/unit/                   # pytest 단위 테스트
├── main.py                       # CLI 엔트리포인트
└── .github/workflows/radar-crawler.yml
```

## ENTITIES

| Entity | Examples |
|--------|----------|
| Vulnerability / DataBreach | CVE, zero-day, ransomware, leaked |
| IncidentDisclosure / ServiceOutage | breach notice, status page, 장애, 점검 |
| EnforcementAction / Compliance | fine, settlement, consent order, 과징금 |

## DEVIATIONS FROM TEMPLATE

- `javascript` 소스로 규제기관 공지와 집행 페이지를 수집한다.
- taxonomy 기준으로 `공식 + 운영 + 커뮤니티` 레이어를 우선 유지한다.
- browser collector 설정(`config`)을 실제 런타임에서 읽도록 확장했다.

## COMMANDS

```bash
python main.py --category trust --recent-days 7
python main.py --category trust --per-source-limit 50 --keep-days 90
pip install 'radar-core[browser]'
```
