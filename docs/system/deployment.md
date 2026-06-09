# 배포 가이드

## 1. GitHub 저장소 생성

```bash
# GitHub에서 저장소 생성 후
git remote add origin https://github.com/[계정명]/ai-webzine.git
git branch -M main
git push -u origin main
```

### GitHub Pages 설정
1. 저장소 → Settings → Pages
2. Source: **GitHub Actions** 선택
3. 이후 `site/` 파일이 push될 때마다 자동 배포

---

## 2. Render.com 관리자 서버 배포

### 가입 및 서비스 생성
1. https://render.com 에서 무료 계정 생성
2. Dashboard → New → Web Service
3. GitHub 저장소 연결: `ai-webzine`
4. 설정:
   - **Name**: ai-webzine-admin
   - **Region**: Singapore (한국과 가장 가까운 무료 리전)
   - **Branch**: main
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `cd admin && uvicorn server:app --host 0.0.0.0 --port $PORT`
   - **Plan**: Free

### 환경 변수 설정 (Environment → Add Environment Variable)
`.env.example` 파일의 항목을 모두 실제 값으로 입력:
- `ANTHROPIC_API_KEY`
- `TAVILY_API_KEY`
- `GMAIL_CLIENT_ID`, `GMAIL_CLIENT_SECRET`, `GMAIL_REFRESH_TOKEN`, `GMAIL_SENDER_ADDRESS`
- `ROUTINE_C_ENDPOINT`, `ROUTINE_C_BEARER_TOKEN` (Routine C 생성 후 입력)
- `ADMIN_SECRET_KEY` (랜덤 32바이트: `python -c "import secrets; print(secrets.token_hex(32))"`)
- `GITHUB_TOKEN` (repo 권한 PAT)
- `GITHUB_REPO` (예: myname/ai-webzine)
- `ADMIN_EMAIL` (관리자 이메일)

> **Render 무료 티어 주의**: 15분간 요청이 없으면 서비스가 슬립 상태로 진입합니다.
> 관리자 페이지 첫 접속 시 ~30초 대기가 발생할 수 있습니다.

---

## 3. Gmail API OAuth2 설정

1. https://console.cloud.google.com → 새 프로젝트 생성
2. API 및 서비스 → API 라이브러리 → **Gmail API** 활성화
3. OAuth 동의 화면 설정 (외부, 개인 사용)
4. 사용자 인증 정보 → OAuth 2.0 클라이언트 ID 생성 (데스크톱 앱)
5. `credentials.json` 다운로드
6. 아래 스크립트로 refresh_token 생성:

```python
from google_auth_oauthlib.flow import InstalledAppFlow
flow = InstalledAppFlow.from_client_secrets_file("credentials.json", ["https://www.googleapis.com/auth/gmail.send"])
creds = flow.run_local_server(port=0)
print("REFRESH_TOKEN:", creds.refresh_token)
```

---

## 4. Claude Code Routines 생성

claude.ai/code → Routines 탭에서 생성:

### Routine A (매주 토요일 17:00 KST)
- **Trigger**: Schedule
- **Schedule**: `0 8 * * 6` (UTC 08:00 = KST 17:00, 토요일)
- **Repository**: ai-webzine
- **Prompt**: "scripts/routine_a_news_search.py를 실행하라. 환경 변수는 Render.com에 설정된 값을 사용한다."
- **Env vars**: ANTHROPIC_API_KEY, TAVILY_API_KEY, GMAIL_*, GITHUB_TOKEN, GITHUB_REPO, ADMIN_EMAIL

### Routine B (매주 월요일 03:00 KST)
- **Schedule**: `0 18 * * 0` (UTC 18:00 = KST 월 03:00, 일요일 UTC)
- **Prompt**: "scripts/routine_b_deep_research.py를 실행하라. status.json이 THEME_PLAN_READY인 경우에만 진행한다."

### Routine C (API 트리거)
- **Trigger**: API
- Routine C 생성 후 나오는 Endpoint URL과 Bearer Token을 환경 변수에 등록

---

## 5. 첫 로그인 및 비밀번호 변경

1. Render.com 배포 URL 접속
2. 아이디: `admin4web` / 비밀번호: `admin1234!`
3. **내 계정** 탭 → 비밀번호 즉시 변경 (필수)

---

## 6. E2E 동작 테스트

```
1. Routine A "Run now" → data/weekly/YYYY-WNN/ 생성 확인
2. 관리자 페이지 → 기사 검토 탭 → 확정 버튼
3. 기획 주제 탭 → 주제 입력 → 등록
4. Routine B "Run now" → 초안 생성 확인
5. 초안 검토 탭 → 미리보기 → 승인 버튼
6. GitHub Pages URL에서 웹진 확인
7. 등록된 수신자 이메일에서 뉴스레터 수신 확인
```
