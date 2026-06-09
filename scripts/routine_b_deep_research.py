"""
Routine B 진입점 — 매주 월요일 03:00 실행

전제 조건: status.json == "THEME_PLAN_READY"

1. theme-plan.json에서 기술/비기술 주제 읽기
2. 기술 분야 기획 보고서 생성 (Claude API)
3. 비기술 분야 기획 보고서 생성 (Claude API)
4. 뉴스레터 HTML 초안 생성
5. 웹진 HTML 초안 생성
6. 관리자에게 검토 요청 이메일 발송
"""

import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

import content_generator
import webzine_builder
from github_helper import GitHubHelper
from gmail_helper import send_admin_notification
from routine_a_news_search import get_week_id


def main() -> None:
    week_id = get_week_id()
    print(f"[Routine B] 시작: {week_id}")

    gh = GitHubHelper()
    weekly_path = f"data/weekly/{week_id}"

    # 전제 조건 확인
    status = gh.read_json(f"{weekly_path}/status.json")
    if not status or status.get("status") != "THEME_PLAN_READY":
        current = status.get("status") if status else "없음"
        print(f"[Routine B] 전제 조건 미충족 (현재 상태: {current}) — 종료")
        admin_email = os.environ.get("ADMIN_EMAIL")
        if admin_email:
            send_admin_notification(
                to=admin_email,
                subject=f"[AI 웹진] {week_id} Routine B 실행 불가",
                body=(
                    f"현재 워크플로 상태: {current}\n"
                    "기획 주제 입력(THEME_PLAN_READY) 후에 Routine B가 실행됩니다.\n"
                    "관리자 페이지에서 기획 주제를 먼저 입력해 주세요."
                ),
            )
        return

    # 기획 주제 읽기
    theme_plan = gh.read_json(f"{weekly_path}/theme-plan.json")
    if not theme_plan:
        print("[Routine B] theme-plan.json 없음 — 종료")
        return

    tech = theme_plan["tech_report"]
    nontech = theme_plan["nontech_report"]

    # 뉴스 후보 읽기
    candidates = gh.read_json(f"{weekly_path}/selected-articles.json")
    if not candidates:
        # 선정 확정 전이면 news-candidates.json 사용
        candidates = gh.read_json(f"{weekly_path}/news-candidates.json") or {}

    # 상태 업데이트
    gh.write_json(f"{weekly_path}/status.json", {
        **status,
        "status": "GENERATING",
        "timeline": {**status.get("timeline", {}), "generating_started": _now()},
    })

    # 1. 기술 분야 기획 보고서 생성
    print("[Routine B] 기술 분야 기획 보고서 생성 중...")
    tech_report = content_generator.generate_theme_report(
        title=tech["title"],
        agenda=tech["agenda"],
        perspective=tech["perspective"],
        theme_area=tech["theme_area"],
    )
    gh.write_text(f"{weekly_path}/draft-tech-report.md", tech_report)
    print("[Routine B] 기술 보고서 생성 완료")

    # 2. 비기술 분야 기획 보고서 생성
    print("[Routine B] 비기술 분야 기획 보고서 생성 중...")
    nontech_report = content_generator.generate_theme_report(
        title=nontech["title"],
        agenda=nontech["agenda"],
        perspective=nontech["perspective"],
        theme_area=nontech["theme_area"],
    )
    gh.write_text(f"{weekly_path}/draft-nontech-report.md", nontech_report)
    print("[Routine B] 비기술 보고서 생성 완료")

    # 3. 뉴스레터 인트로 생성
    topics = candidates.get("topics_covered", [])
    intro_text = content_generator.generate_newsletter_intro(
        week_id=week_id,
        tech_report_title=tech["title"],
        nontech_report_title=nontech["title"],
        article_count=len(candidates.get("selected", [])),
        topics_covered=topics,
    )

    # 4. 뉴스레터 HTML 초안 빌드
    newsletter_html = webzine_builder.build_newsletter_html(
        week_id=week_id,
        candidates=candidates,
        tech_report=tech_report,
        nontech_report=nontech_report,
        intro_text=intro_text,
    )
    gh.write_text(f"{weekly_path}/draft-newsletter.html", newsletter_html)

    # 5. 웹진 HTML 초안 빌드
    webzine_html = webzine_builder.build_webzine(
        week_id=week_id,
        candidates=candidates,
        tech_report=tech_report,
        nontech_report=nontech_report,
    )
    gh.write_text(f"{weekly_path}/draft-webzine.html", webzine_html)

    # 6. 상태 업데이트: DRAFT_READY
    gh.write_json(f"{weekly_path}/status.json", {
        **status,
        "status": "DRAFT_READY",
        "timeline": {
            **status.get("timeline", {}),
            "generating_started": status.get("timeline", {}).get("generating_started", _now()),
            "draft_ready": _now(),
        },
    })

    # 7. 관리자 알림
    admin_email = os.environ.get("ADMIN_EMAIL")
    if admin_email:
        send_admin_notification(
            to=admin_email,
            subject=f"[AI 웹진] {week_id} 초안 준비 완료 — 검토 및 승인 요청",
            body=(
                f"이번 주({week_id}) 기획 보고서 2편 및 뉴스레터 초안이 준비되었습니다.\n\n"
                f"기술 분야: {tech['title']}\n"
                f"비기술 분야: {nontech['title']}\n\n"
                "관리자 페이지에서 초안을 검토하고 승인해 주세요.\n"
                "승인 즉시 웹진 배포 및 뉴스레터 발송이 시작됩니다."
            ),
        )

    print(f"[Routine B] 완료: {week_id}")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


if __name__ == "__main__":
    main()
