# AI 웹진 자동화 프로젝트 — Claude Code 운영 규칙

## 프로젝트 개요
정보시스템 감리 종사자 대상 주간 AI 동향 웹진(GitHub Pages) + 뉴스레터(Gmail) 자동 발행 시스템.

@docs/system/architecture.md
@docs/content/topic-areas.md
@docs/principles.md

## NEVER TOUCH 목록
아래 파일은 이유 없이 수정 금지. 의도적 수정 시 작업 전 반드시 확인 요청.
- `data/members.json` — 관리자 계정 정보
- `data/recipients.json` — 뉴스레터 수신자 목록
- `.env` — 환경 변수 (API 키)
- `.git/hooks/pre-commit` — 안전장치 훅 자체
- `docs/decisions/DONE.md` — 완료 이력

## 세션 시작 규칙
1. `docs/decisions/PENDING.md` 먼저 확인
2. 미반영 항목(체크박스 미완료) 있으면 사용자에게 보고 후 작업 시작
3. 최신 주차 상태: `data/weekly/` 가장 최신 디렉토리의 `status.json` 확인

## 작업 전 확인 요청 조건
- 파일 3개 이상 동시 수정
- 함수 시그니처 변경
- 외부 서비스(API, OAuth) 연동 추가

## 결정 기록 규칙
- 대화 중 기준 확정 즉시 `docs/decisions/PENDING.md`에 DEC-NNN ID로 기록
- 커밋 메시지 형식: `[DEC-NNN] 내용 요약`
- 1결정 1커밋 원칙
- 모든 체크리스트 완료 후에만 DONE.md로 이동

## 롤백 규칙
롤백 요청 수신 시 영향 범위를 분석하고 사용자 확인 후 실행.
