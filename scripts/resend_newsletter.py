"""
뉴스레터 재발송 복구 도구 — 발송 실패한 주차의 뉴스레터만 다시 보낸다.

Routine C는 status가 PUBLISHED면 종료하므로(웹진 재배포 방지) 발송만 실패한
경우 재시도 경로가 없다. 이 스크립트는 웹진을 재빌드/재배포하지 않고
이미 GitHub에 커밋된 해당 주차 데이터로 뉴스레터 HTML을 생성하여
active 수신자에게만 재발송한다.

사용법:
  python scripts/resend_newsletter.py 2026-W24            # 실제 발송
  python scripts/resend_newsletter.py 2026-W24 --dry-run  # 발송 없이 미리보기
  python scripts/resend_newsletter.py 2026-W24 --to a@b.com  # 특정 주소로만(테스트)

환경 변수: GITHUB_TOKEN, GITHUB_REPO, GMAIL_* (.env 또는 클라우드 env)
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

import webzine_builder
from github_helper import GitHubHelper
from gmail_helper import send_newsletter


def _subject(week_id: str) -> str:
    now = datetime.now(timezone.utc)
    year, wnum = week_id.split("-W")
    week_label = f"{year}년 제{int(wnum)}호"
    date_str = now.strftime("%Y년 %m월")
    return f"[AI 웹진 {week_label}] 이번 주 AI 동향 — {date_str}"


def main() -> int:
    args = sys.argv[1:]
    if not args:
        print("사용법: python scripts/resend_newsletter.py <YYYY-WNN> [--dry-run] [--to addr]")
        return 1

    week_id = args[0]
    dry_run = "--dry-run" in args
    override_to = None
    if "--to" in args:
        override_to = args[args.index("--to") + 1]

    gh = GitHubHelper()

    # 1. 뉴스레터 HTML 생성 (GitHub의 해당 주차 데이터 기반, 재배포 없음)
    html = webzine_builder.build_newsletter_html(week_id)
    print(f"[resend] {week_id} 뉴스레터 HTML 생성 완료 (길이 {len(html)})")

    # 2. 수신자 결정
    if override_to:
        recipients = [override_to]
    else:
        data = gh.read_json("data/recipients.json") or {}
        recipients = [
            r["email"] for r in data.get("recipients", [])
            if r.get("active", True)
        ]
    print(f"[resend] 대상 수신자 {len(recipients)}명: {recipients}")

    if dry_run:
        print("[resend] --dry-run: 실제 발송하지 않고 종료")
        return 0

    if not recipients:
        print("[resend] active 수신자 없음 — 종료")
        return 0

    # 3. 발송
    result = send_newsletter(recipients, _subject(week_id), html)
    print(f"[resend] 발송 완료: 성공 {len(result['sent'])}명, 실패 {len(result['failed'])}명")
    if result["failed"]:
        print(f"[resend] 실패 목록: {result['failed']}")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
