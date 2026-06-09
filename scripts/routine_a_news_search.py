"""
Routine A 진입점 — 매주 토요일 17:00 실행

1. 11개 토픽 영역 뉴스 검색 (RSS 피드, API 키 불필요)
2. 12개 기사 선정 + 여분 3개 (휴리스틱 점수화)
3. data/weekly/YYYY-WNN/ 디렉토리에 결과 저장 (GitHub API)
4. Claude Code 세션이 제목·요약 한글 번역 후 JSON 업데이트
5. 관리자에게 이메일 알림
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# 스크립트 디렉토리를 모듈 경로에 추가
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv

load_dotenv()

import article_curator
import news_searcher
from github_helper import GitHubHelper
from gmail_helper import send_admin_notification


def get_week_id(dt: datetime | None = None) -> str:
    """현재 주차 ID를 YYYY-WNN 형식으로 반환한다."""
    dt = dt or datetime.now(timezone.utc)
    return f"{dt.year}-W{dt.isocalendar()[1]:02d}"


def main() -> None:
    week_id = get_week_id()
    print(f"[Routine A] 시작: {week_id}")

    gh = GitHubHelper()
    weekly_path = f"data/weekly/{week_id}"

    # 이미 완료된 주차면 건너뜀
    status = gh.read_json(f"{weekly_path}/status.json")
    if status and status.get("status") not in (None, "IDLE", "NEWS_SEARCHING"):
        print(f"[Routine A] 이미 진행 중인 상태: {status.get('status')} — 종료")
        return

    # 상태 업데이트: NEWS_SEARCHING
    gh.write_json(f"{weekly_path}/status.json", {
        "week": week_id,
        "status": "NEWS_SEARCHING",
        "timeline": {"news_search_started": _now()},
    })

    # 1. 뉴스 검색
    print("[Routine A] 뉴스 검색 중...")
    all_articles = news_searcher.search_all_topics(days_back=7, max_per_topic=5)
    total = sum(len(v) for v in all_articles.values())
    print(f"[Routine A] 총 {total}건 수집 완료")

    # 2. 기사 선정
    print("[Routine A] 기사 선정 중 (휴리스틱 점수화)...")
    selected, spare = article_curator.curate(all_articles, select_count=12, spare_count=3)
    print(f"[Routine A] 선정 {len(selected)}건 + 여분 {len(spare)}건")

    # 토픽 커버리지 확인
    topics_covered = list({a.topic_tag for a in selected})
    if len(topics_covered) < 3:
        print(f"[WARN] 토픽 커버리지 부족: {topics_covered}")

    # 3. 결과 저장 (GitHub API)
    candidates_data = {
        "week": week_id,
        "generated_at": _now(),
        "topics_covered": topics_covered,
        "selected": [article_curator.to_dict(a) for a in selected],
        "spare": [article_curator.to_dict(a) for a in spare],
    }
    gh.write_json(f"{weekly_path}/news-candidates.json", candidates_data)

    # 상태 업데이트: AWAITING_ADMIN_REVIEW
    gh.write_json(f"{weekly_path}/status.json", {
        "week": week_id,
        "status": "AWAITING_ADMIN_REVIEW",
        "timeline": {
            "news_search_started": status.get("timeline", {}).get("news_search_started", _now()) if status else _now(),
            "news_search_completed": _now(),
        },
        "topics_covered": topics_covered,
        "selected_count": len(selected),
    })

    # 4. 관리자 알림
    admin_email = os.environ.get("ADMIN_EMAIL")
    if admin_email:
        send_admin_notification(
            to=admin_email,
            subject=f"[AI 웹진] {week_id} 뉴스 후보 {len(selected)}건 준비됨",
            body=_build_notification_body(week_id, selected, topics_covered),
        )

    print(f"[Routine A] 완료: {week_id}")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _build_notification_body(week_id: str, selected, topics_covered: list[str]) -> str:
    lines = [
        f"이번 주({week_id}) AI 뉴스 후보 {len(selected)}건이 준비되었습니다.",
        f"커버된 토픽: {', '.join(topics_covered)}",
        "",
        "주요 기사 목록:",
    ]
    for i, a in enumerate(selected[:5], 1):
        lines.append(f"  {i}. [{a.topic_tag}] {a.title}")
    lines.append("  ...")
    lines.append("")
    lines.append("관리자 페이지에서 검토 후 확정해 주세요.")
    return "\n".join(lines)


if __name__ == "__main__":
    main()
