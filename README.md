# TrustRadar - 신뢰도 정보 레이더

**🌐 Live Report**: https://ai-frendly-datahub.github.io/TrustRadar/


보안, 개인정보, 규제 집행, 소비자 신뢰 신호를 함께 수집해 기업별 trust/compliance risk를 추적합니다.

## 프로젝트 목표

- **데이터 수집**: 보안 미디어, 규제기관 공지, 집행/사고 공시, 커뮤니티 신호
- **엔티티 분석**: 산업별 키워드 매칭 (금융, 전자상거래, 통신 등)
- **트렌드 리포트**: DuckDB 저장 + HTML 리포트로 {domain} 동향 시각화
- **자동화**: GitHub Actions 일일 수집 + GitHub Pages 리포트 자동 배포

## 기술적 우수성

- **안정성**: HTTP 자동 재시도(지수 백오프), DB 트랜잭션 에러 처리
- **관찰성**: 구조화된 JSON 로깅으로 파이프라인 상태 실시간 모니터링
- **품질 보증**: 단위 테스트로 코드 변경 시 회귀 버그 사전 차단
- **고성능**: 배치 처리 최적화로 대량 데이터 수집 시 성능 향상
- **운영 자동화**: Email/Webhook 알림으로 무인 운영 가능

## 빠른 시작

1. 가상환경을 만들고 의존성을 설치합니다.
   ```bash
   pip install -r requirements.txt
   ```

2. 실행:
   ```bash
   python main.py --category trust --recent-days 7
   # 리포트: reports/trust_report.html
   ```

   주요 옵션: `--per-source-limit 20`, `--recent-days 5`, `--keep-days 60`, `--timeout 20`.

## 소스 전략

- `공식`: KISA, PIPC, FTC 집행/가이드 페이지
- `시장`: BleepingComputer, Dark Reading, CIRCL, 보안 전문 미디어
- `커뮤니티`: Hacker News 기반 practitioner discussion signal
- `운영`: incident disclosure, enforcement action, complaint/remediation 서사를 잡는 공지형 소스

JavaScript/browser 소스를 제대로 수집하려면 `pip install 'radar-core[browser]'`가 필요합니다.

## 데이터 품질 운영

- `config/categories/trust.yaml`의 `data_quality`는 `incident_disclosure`, `status_page_incident`, `enforcement_action`, `consumer_complaint`, `ai_asset_risk` 이벤트를 분리합니다.
- `trustradar.trust_signals`는 사고 상태, 집행 결과, AI 자산 리스크, 검증 상태를 `matched_entities`의 `IncidentStatus`, `EnforcementOutcome`, `AIAssetRisk`, `OperationalEvent`, `VerificationState`로 보강합니다.
- 커뮤니티/시장 소스는 `requires_official_confirmation` 또는 `corroborating_report` 역할로만 병합하고, KISA/PIPC/FTC/CFPB/CIRCL 같은 공식 소스를 기준점으로 둡니다.
- `source_backlog`의 vendor status page, breach notice portal, CFPB complaint 후보는 service id, incident permalink, 개인정보 비식별성, parser 검증 전까지 기본 비활성 후보로 둡니다.

## GitHub Actions & GitHub Pages

- 워크플로: `.github/workflows/radar-crawler.yml`
  - 스케줄: 매일 00:00 UTC (KST 09:00), 수동 실행도 지원.
  - 환경 변수 `RADAR_CATEGORY`를 프로젝트에 맞게 수정하세요.
  - 리포트 배포 디렉터리: `reports` → `gh-pages` 브랜치로 배포.
  - DuckDB 경로: `data/radar_data.duckdb` (Pages에 올라가지 않음). 아티팩트로 7일 보관.

- 설정 방법:
  1) 저장소 Settings → Pages에서 `gh-pages` 브랜치를 선택해 활성화
  2) Actions 권한을 기본값으로 두거나 외부 PR에서도 실행되도록 설정
  3) 워크플로 파일의 `RADAR_CATEGORY`를 원하는 YAML 이름으로 변경

## 동작 방식

- **수집**: 카테고리 YAML에 정의된 소스를 수집합니다. 실행 시 DuckDB에 적재하고 보존 기간(`keep_days`)을 적용합니다.
- **분석**: 엔티티별 키워드 매칭. 매칭된 키워드를 리포트에 칩으로 표시합니다.
- **리포트**: `reports/<category>_report.html`을 생성하며, 최근 N일(기본 7일) 기사와 엔티티 히트 카운트, 수집 오류를 표시합니다.

## 기본 경로

- DB: `data/radar_data.duckdb`
- 리포트 출력: `reports/`

## 디렉터리 구성

```
TrustRadar/
  main.py                 # CLI 엔트리포인트
  requirements.txt        # 의존성
  config/
    config.yaml           # DB/리포트 경로 설정
    categories/
      trust.yaml  # 소스 + 엔티티 정의
  trustradar/
    collector.py          # 데이터 수집
    analyzer.py           # 엔티티 태깅
    reporter.py           # HTML 렌더링
    storage.py            # DuckDB 저장/정리
    config_loader.py      # YAML 로더
    models.py             # 데이터 클래스
  .github/workflows/      # GitHub Actions (crawler + Pages 배포)
```

<!-- DATAHUB-OPS-AUDIT:START -->
## DataHub Operations

- CI/CD workflows: `pr-checks.yml`, `radar-crawler.yml`, `release.yml`.
- GitHub Pages visualization: `reports/index.html` (valid HTML); https://ai-frendly-datahub.github.io/TrustRadar/.
- Latest remote Pages check: HTTP 200, HTML.
- Local workspace audit: 58 Python files parsed, 0 syntax errors.
- Re-run audit from the workspace root: `python scripts/audit_ci_pages_readme.py --syntax-check --write`.
- Latest audit report: `_workspace/2026-04-14_github_ci_pages_readme_audit.md`.
- Latest Pages URL report: `_workspace/2026-04-14_github_pages_url_check.md`.
<!-- DATAHUB-OPS-AUDIT:END -->
