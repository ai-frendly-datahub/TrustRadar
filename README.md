# TrustRadar

TrustRadar는 리뷰/평판 이슈를 모니터링하는 경량 레이더 프로젝트입니다.
`python main.py --category trust`를 실행하면 RSS 수집 -> 엔티티 키워드 매칭 -> DuckDB 저장 ->
HTML 리포트 생성까지 한 번에 수행합니다.

## 빠른 시작
1. 의존성 설치
   ```bash
   pip install -r requirements.txt
   ```
2. 실행
   ```bash
   python main.py --category trust --recent-days 7
   ```
3. 결과 확인
   - 리포트: `reports/trust_report.html`
   - DB: `data/trustradar_data.duckdb`

## 기본 카테고리
`config/categories/trust.yaml`
- 소스: TechCrunch, The Verge, Consumer Reports (RSS)
- 엔티티: ReviewQuality, Rating, Complaint, Platform, Reputation
- 목적: 가짜 리뷰, 컴플레인, 평점 흐름, 플랫폼 언급, 평판 위기 신호 추적

## MCP 서버 도구
`trustradar/mcp_server/server.py`
- `search`: 자연어 질의 기반 FTS 검색
- `recent_updates`: 최근 수집 기사 조회
- `sql`: DuckDB 읽기 전용 SQL 실행
- `top_trends`: 엔티티 언급량 집계
- `trust_score`: 최근 기사 엔티티 기준 신뢰도 점수 계산

## GitHub Actions
워크플로: `.github/workflows/radar-crawler.yml`
- 이름: `TrustRadar Crawler`
- 기본 카테고리: `RADAR_CATEGORY=trust`
- 실행: 매일 00:00 UTC + 수동 실행
- 산출물: `reports/`를 `gh-pages`로 배포, DuckDB 아티팩트 업로드
