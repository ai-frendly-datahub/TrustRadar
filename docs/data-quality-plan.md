# Data Quality Plan

- 생성 시각: `2026-04-11T16:05:37.910248+00:00`
- 우선순위: `P0`
- 데이터 품질 점수: `98`
- 가장 약한 축: `추적성`
- Governance: `high`
- Primary Motion: `compliance-risk`

## 현재 이슈

- 현재 설정상 즉시 차단 이슈 없음. 운영 지표와 freshness SLA만 명시하면 됨

## 필수 신호

- 침해사고 disclosure와 보안 공지
- status page incident와 서비스 장애 이력
- 규제기관 enforcement와 소비자 complaint

## 품질 게이트

- 사고 발생일·공개일·해결일을 별도 필드로 유지
- 취약점/장애/개인정보 사건을 같은 incident로 병합하지 않음
- 공식 disclosure 없는 커뮤니티 신호는 확인 필요 상태로 표시

## 다음 구현 순서

- incident_disclosure와 status_page_incident freshness/stale 리포트를 검증 산출물에 추가
- status page·breach notice·consumer complaint 후보는 source_backlog에서 parser·개인정보·service id mapping 검증 후 단계적 활성화
- incident severity scoring에 VerificationState·공식 근거 URL·AIAssetRisk를 함께 표시

## 운영 규칙

- 원문 URL, 수집일, 이벤트 발생일은 별도 필드로 유지한다.
- 공식 source와 커뮤니티/시장 source를 같은 신뢰 등급으로 병합하지 않는다.
- collector가 인증키나 네트워크 제한으로 skip되면 실패를 숨기지 말고 skip 사유를 기록한다.
- 이 문서는 `scripts/build_data_quality_review.py --write-repo-plans`로 재생성한다.
