# Business Quality Upgrade

- Generated: `2026-04-14T04:48:11.525239+00:00`
- Portfolio verdict: `충분`
- Business value score: `89.1`
- Upgrade phase: P0 사고/상태 근거 강화
- Primary motion: `compliance-risk`
- Weakest dimension: `traceability`

## Current Evidence

- Primary rows: `1852`
- Today raw rows: `39`
- Latest report items: `37`
- Match rate: `97.3%`
- Collection errors: `0`
- Freshness gap: `6`

## Upgrade Actions

- incident_disclosure와 status_page_incident의 freshness SLA를 status page/service id 기준으로 점검한다.
- 커뮤니티/민원 신호는 official_confirmation_required 상태로 분리해 공식 공지와 같은 근거로 병합하지 않는다.
- service id canonicalization과 breach/status notice evidence URL 검증을 다음 활성화 게이트로 둔다.

## Quality Contracts

- `config/categories/trust.yaml`: output `reports/trust_quality.json`, tracked `incident_disclosure, status_page_incident, enforcement_action, consumer_complaint, ai_asset_risk`, backlog items `5`

## Contract Gaps

- None.
