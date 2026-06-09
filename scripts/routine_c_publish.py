"""
Routine C 진입점 — 관리자 승인 즉시 API 트리거로 실행

1. approval.json 존재 및 유효성 확인
2. webzine_builder.build() → site/issues/YYYY-WNN/index.html GitHub 커밋
3. GitHub Pages 자동 배포 (deploy-pages.yml 트리거됨)
4. 수신자 전체에 뉴스레터 발송 (Resend API)
5. status.json → PUBLISHED, 관리자 발행 완료 알림

원자성 보장: 웹진 빌드 실패 시 뉴스레터 발송하지 않음.
"""

import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

import webzine_builder
from github_helper import GitHubHelper
from gmail_helper import send_newsletter, send_admin_notification
from routine_a_news_search import get_week_id


def main() -> None:
    week_id = get_week_id()
    print(f"[Routine C] 발행 시작: {week_id}")

    gh = GitHubHelper()
    weekly_path = f"data/weekly/{week_id}"

    # 1. 승인 확인
    approval = gh.read_json(f"{weekly_path}/approval.json")
    if not approval or not approval.get("approved"):
        print("[Routine C] 승인 정보 없음 — 종료")
        return

    status = gh.read_json(f"{weekly_path}/status.json") or {}
    if status.get("status") == "PUBLISHED":
        print("[Routine C] 이미 발행됨 — 종료")
        return

    # 상태: PUBLISHING
    gh.write_json(f"{weekly_path}/status.json", {
        **status,
        "status": "PUBLISHING",
        "timeline": {**status.get("timeline", {}), "publishing_started": _now()},
    }, "auto: 발행 시작")

    # 2. 웹진 빌드 + GitHub 커밋 (→ GitHub Pages 자동 배포)
    print("[Routine C] 웹진 빌드 중...")
    try:
        webzine_builder.build(week_id)
        print("[Routine C] 웹진 빌드 완료 → GitHub Pages 배포 시작됨")
    except Exception as exc:
        print(f"[Routine C] 웹진 빌드 실패: {exc} — 뉴스레터 발송 중단")
        gh.write_json(f"{weekly_path}/status.json", {
            **status,
            "status": "PUBLISH_FAILED",
            "error": str(exc),
            "timeline": {**status.get("timeline", {}), "failed": _now()},
        }, "auto: 발행 실패")
        return

    # 3. 뉴스레터 HTML 준비 (저장된 초안 또는 빌더로 생성)
    newsletter_html = gh.read_text(f"{weekly_path}/draft-newsletter.html") or ""
    if not newsletter_html:
        print("[Routine C] draft-newsletter.html 없음 → 뉴스레터 HTML 자동 생성")
        newsletter_html = webzine_builder.build_newsletter_html(week_id)

    # 4. 수신자 목록 읽기
    recipients_data = gh.read_json("data/recipients.json") or {}
    active_recipients = [
        r["email"]
        for r in recipients_data.get("recipients", [])
        if r.get("active", True)
    ]

    # 5. 뉴스레터 발송
    now = datetime.now(timezone.utc)
    year, wnum = week_id.split("-W")
    week_label = f"{year}년 제{int(wnum)}호"
    date_str = now.strftime("%Y년 %m월")
    subject = f"[AI 웹진 {week_label}] 이번 주 AI 동향 — {date_str}"

    result = {"sent": [], "failed": []}
    if active_recipients and newsletter_html:
        print(f"[Routine C] 뉴스레터 {len(active_recipients)}명 발송 중...")
        result = send_newsletter(active_recipients, subject, newsletter_html)
        print(f"[Routine C] 발송 완료: 성공 {len(result['sent'])}명, 실패 {len(result['failed'])}명")
    else:
        print("[Routine C] 수신자 없거나 뉴스레터 없음 — 발송 건너뜀")

    # 6. 상태 PUBLISHED
    gh.write_json(f"{weekly_path}/status.json", {
        **status,
        "status": "PUBLISHED",
        "timeline": {
            **status.get("timeline", {}),
            "publishing_started": status.get("timeline", {}).get("publishing_started", _now()),
            "published": _now(),
        },
        "newsletter_sent": len(result["sent"]),
        "newsletter_failed": len(result["failed"]),
    }, "auto: 발행 완료")

    # 7. 관리자 알림
    admin_email = os.environ.get("ADMIN_EMAIL", "")
    if admin_email:
        repo = os.environ.get("GITHUB_REPO", "")
        owner = repo.split("/")[0] if "/" in repo else ""
        repo_name = repo.split("/")[1] if "/" in repo else repo
        pages_url = f"https://{owner}.github.io/{repo_name}/issues/{week_id}/"
        send_admin_notification(
            to=admin_email,
            subject=f"[AI 웹진] {week_label} 발행 완료",
            body=(
                f"{week_label}({week_id}) 발행이 완료되었습니다.\n\n"
                f"웹진 URL: {pages_url}\n"
                f"뉴스레터: {len(result['sent'])}명 발송 성공"
                + (f", {len(result['failed'])}명 실패" if result["failed"] else "")
            ),
        )

    print(f"[Routine C] 완료: {week_id}")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


if __name__ == "__main__":
    main()
