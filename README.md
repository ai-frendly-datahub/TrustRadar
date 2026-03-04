# TrustRadar

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

리뷰 품질, 평판 관리, 가짜 리뷰 감지 관련 뉴스를 자동 수집하고 신뢰 점수 트렌드를 분석하는 레이더 프로젝트입니다.

## 프로젝트 목표

- **리뷰 품질 모니터링**: 가짜 리뷰, 리뷰 조작, 평점 신뢰도 관련 뉴스를 일일 자동 수집
- **평판 트렌드 추적**: 브랜드 이미지, PR 위기, 평판 관리 사례 등 평판 관련 동향 파악
- **신뢰 점수 분석**: MCP `trust_score` 도구로 리뷰/평판 관련 긍정/부정 신호를 자동 분석하여 신뢰 점수 산출
- **플랫폼 비교**: Yelp, Google Reviews, Trustpilot 등 리뷰 플랫폼별 트렌드 비교
- **AI 신뢰 도우미**: MCP 서버를 통해 AI 어시스턴트에서 리뷰/평판 정보를 자연어로 검색

## 주요 기능

1. **RSS 자동 수집**: TechCrunch, The Verge, Consumer Reports 등에서 리뷰 관련 기사 수집
2. **엔티티 매칭**: 리뷰 품질, 평점/등급, 불만/컴플레인, 리뷰 플랫폼, 평판 관리 5개 카테고리
3. **DuckDB 저장**: UPSERT 시맨틱 기반 기사 저장
4. **JSONL 원본 보존**: `data/raw/YYYY-MM-DD/{source}.jsonl`
5. **SQLite FTS5 검색**: 전문검색으로 리뷰 관련 빠른 검색
6. **자연어 쿼리**: "최근 2주 가짜 리뷰 관련" 같은 자연어 검색
7. **HTML 리포트**: 카테고리별 신뢰 점수가 포함된 자동 리포트
8. **MCP 서버**: search, recent_updates, sql, top_trends, trust_score

## 빠른 시작

```bash
pip install -r requirements.txt
python main.py --category trust --recent-days 7
```

- 리포트: `reports/trust_report.html`
- DB: `data/radar_data.duckdb`

## 프로젝트 구조

```
TrustRadar/
├── trustradar/
│   ├── collector.py       # RSS 수집
│   ├── analyzer.py        # 엔티티 키워드 매칭
│   ├── storage.py         # DuckDB 스토리지
│   ├── reporter.py        # HTML 리포트
│   ├── raw_logger.py      # JSONL 원본 기록
│   ├── search_index.py    # SQLite FTS5
│   ├── nl_query.py        # 자연어 쿼리 파서
│   └── mcp_server/        # MCP 서버 (5개 도구)
├── config/categories/trust.yaml
├── tests/
├── .github/workflows/
└── main.py
```

## MCP 서버 도구

| 도구 | 설명 |
|------|------|
| `search` | FTS5 기반 자연어 검색 |
| `recent_updates` | 최근 수집 기사 조회 |
| `sql` | 읽기 전용 SQL 쿼리 |
| `top_trends` | 엔티티 언급 빈도 트렌드 |
| `trust_score` | 신뢰 점수 트렌드 분석 |

## 테스트

```bash
pytest tests/ -v
```

## CI/CD

- `.github/workflows/radar-crawler.yml`: 매일 00:00 UTC 자동 수집
- GitHub Pages로 리포트 자동 배포
