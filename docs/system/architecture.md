# 시스템 아키텍처

## 구성도
```
[Anthropic Cloud]               [GitHub]                 [Render.com]
Claude Code Routines            ai-webzine 저장소          FastAPI 관리자 서버
  Routine A: 토요일 17:00  ←→   ├── data/                (무료 티어)
    뉴스 검색·큐레이션             ├── scripts/             - 관리자 웹 UI
  Routine B: 월요일 03:00  ←→   ├── site/ (웹진)          - 승인 워크플로
    Deep Research·콘텐츠 생성     └── admin/               - Routine C 트리거
  Routine C: 승인 시 API 트리거
    웹진 배포 + 뉴스레터 발송

                                [GitHub Pages]
                                  site/ → 공개 웹진
```

## 데이터 흐름
1. Routine A → GitHub repo에 `data/weekly/YYYY-WNN/` 커밋
2. 관리자 → Render.com FastAPI 서버에서 검토·승인
3. FastAPI 서버 → GitHub API(PyGitHub)로 파일 읽기/쓰기
4. 관리자 승인 → FastAPI가 Routine C API 트리거 호출
5. Routine C → `site/` 빌드 후 GitHub 푸시 → GitHub Pages 자동 배포
6. Routine C → Gmail API로 수신자 뉴스레터 발송

## 워크플로 상태 전이
```
IDLE → NEWS_SEARCHING → AWAITING_ADMIN_REVIEW → ARTICLES_CONFIRMED
     → THEME_PLAN_READY → GENERATING → DRAFT_READY
     → PUBLISHING → PUBLISHED
```

## 서버 의존성
- Routines: Anthropic Cloud (PC 불필요)
- 관리자 서버: Render.com (PC 불필요)
- 웹진: GitHub Pages (PC 불필요)
- 뉴스레터: Gmail API (PC 불필요)

## 환경 변수 목록
`ANTHROPIC_API_KEY`, `TAVILY_API_KEY`,
`GMAIL_CLIENT_ID`, `GMAIL_CLIENT_SECRET`, `GMAIL_REFRESH_TOKEN`, `GMAIL_SENDER_ADDRESS`,
`ROUTINE_C_ENDPOINT`, `ROUTINE_C_BEARER_TOKEN`,
`ADMIN_SECRET_KEY`, `GITHUB_TOKEN`, `GITHUB_REPO`
