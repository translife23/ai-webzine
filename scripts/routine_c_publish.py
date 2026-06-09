"""
Routine C 진입점 — 관리자 승인 즉시 API 트리거로 실행

1. approval.json 존재 및 유효성 확인
2. 웹진 최종 HTML 빌드 → site/issues/{week_id}/index.html 저장
3. site/archive/index.html 업데이트
4. GitHub 저장소 site/ 변경 → GitHub Pages 자동 배포
5. 수신자 전체에 뉴스레터 발송 (Gmail API)
6. 상태 PUBLISHED로 갱신, 관리자 발행 완료 알림

원자성 보장: 웹진 배포 실패 시 뉴스레터 발송 안 함.
"""

import json
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


def _get_issue_number(week_id: str) -> int:
    try:
        year, week = week_id.split("-W")
        return (int(year) - 2026) * 52 + int(week)
    except Exception:
        return 1


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

    # 상태 업데이트: PUBLISHING
    gh.write_json(f"{weekly_path}/status.json", {
        **status,
        "status": "PUBLISHING",
        "timeline": {**status.get("timeline", {}), "publishing_started": _now()},
    })

    # 2. 최종 콘텐츠 읽기 (승인 후 수정 반영)
    candidates = gh.read_json(f"{weekly_path}/selected-articles.json") \
              or gh.read_json(f"{weekly_path}/news-candidates.json") or {}

    tech_report = gh.read_text(f"{weekly_path}/draft-tech-report.md") or ""
    nontech_report = gh.read_text(f"{weekly_path}/draft-nontech-report.md") or ""
    newsletter_html = gh.read_text(f"{weekly_path}/draft-newsletter.html") or ""

    # 3. 최종 웹진 HTML 빌드
    print("[Routine C] 웹진 HTML 빌드 중...")
    webzine_html = webzine_builder.build_webzine(
        week_id=week_id,
        candidates=candidates,
        tech_report=tech_report,
        nontech_report=nontech_report,
    )

    # 4. GitHub 저장소에 웹진 파일 저장 → GitHub Pages 자동 배포
    issue_path = f"site/issues/{week_id}/index.html"
    print(f"[Routine C] GitHub 저장소에 {issue_path} 저장 중...")
    try:
        gh.write_html(
            issue_path,
            webzine_html,
            message=f"publish: {week_id} 웹진 제{_get_issue_number(week_id)}호",
        )
        print("[Routine C] 웹진 저장 완료 → GitHub Pages 자동 배포 시작")
    except Exception as exc:
        print(f"[Routine C] 웹진 저장 실패: {exc} — 뉴스레터 발송 중단")
        gh.write_json(f"{weekly_path}/status.json", {
            **status,
            "status": "PUBLISH_FAILED",
            "error": str(exc),
        })
        return

    # archive 페이지 업데이트
    _update_archive(gh, week_id)

    # 5. 뉴스레터 발송
    recipients_data = gh.read_json("data/recipients.json") or {}
    active_recipients = [
        r["email"]
        for r in recipients_data.get("recipients", [])
        if r.get("active", True)
    ]

    issue_num = _get_issue_number(week_id)
    date_str = datetime.now(timezone.utc).strftime("%Y년 %m월")
    week_num = week_id.split("-W")[1]
    subject = f"[AI 웹진 제{issue_num}호] 이번 주 AI 동향 — {date_str} {week_num}주"

    result = {"sent": [], "failed": []}
    if active_recipients and newsletter_html:
        print(f"[Routine C] 뉴스레터 {len(active_recipients)}명에게 발송 중...")
        result = send_newsletter(active_recipients, subject, newsletter_html)
        print(f"[Routine C] 발송 완료: 성공 {len(result['sent'])}명, 실패 {len(result['failed'])}명")
    else:
        print("[Routine C] 수신자 없거나 뉴스레터 HTML 없음 — 발송 건너뜀")

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
    })

    # 7. 관리자 발행 완료 알림
    admin_email = os.environ.get("ADMIN_EMAIL")
    if admin_email:
        repo = os.environ.get("GITHUB_REPO", "")
        pages_url = f"https://{repo.split('/')[0]}.github.io/{repo.split('/')[1]}/issues/{week_id}/" if repo else ""
        send_admin_notification(
            to=admin_email,
            subject=f"[AI 웹진] 제{issue_num}호 발행 완료",
            body=(
                f"제{issue_num}호({week_id}) 발행이 완료되었습니다.\n\n"
                f"웹진 URL: {pages_url}\n"
                f"뉴스레터 발송: {len(result['sent'])}명 성공"
                + (f", {len(result['failed'])}명 실패" if result["failed"] else "")
            ),
        )

    print(f"[Routine C] 발행 완료: {week_id}")


def _update_archive(gh: GitHubHelper, new_week_id: str) -> None:
    """archive/index.html에 새로 발행된 호를 추가한다."""
    try:
        html = gh.read_text("site/archive/index.html") or ""
        issue_num = _get_issue_number(new_week_id)
        pub_date = datetime.now(timezone.utc).strftime("%Y년 %m월 %d일")
        new_item = (
            f'<a href="../issues/{new_week_id}/" class="article-card" style="text-decoration:none">'
            f'<span class="topic-tag" style="background:#1A56DB">제{issue_num}호</span>'
            f'<h3 class="article-title">{new_week_id}</h3>'
            f'<p class="article-summary">발행일: {pub_date}</p>'
            f'</a>'
        )
        placeholder = '<p style="color:#64748B">아직 발행된 호가 없습니다.</p>'
        if placeholder in html:
            html = html.replace(placeholder, new_item)
        else:
            html = html.replace('<div id="archive-list"', f'<div id="archive-list">\n        {new_item}', 1)
        gh.write_html("site/archive/index.html", html, message=f"archive: {new_week_id} 추가")
    except Exception as exc:
        print(f"[Routine C] archive 업데이트 실패 (무시): {exc}")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


if __name__ == "__main__":
    main()
