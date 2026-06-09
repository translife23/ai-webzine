"""
Routine A 진입점 — 매주 토요일 17:00 실행

1. 11개 토픽 영역별 해외 1건 + 국내 1건 검색 (총 22건, WebSearch)
2. 제목·요약 한글 번역
3. data/weekly/YYYY-WNN/ 에 결과 저장 후 자동 확정(ARTICLES_CONFIRMED)
4. 관리자에게 이메일 알림
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from github_helper import GitHubHelper
from gmail_helper import send_admin_notification
from news_searcher import TOPIC_QUERIES


def get_week_id(dt: datetime | None = None) -> str:
    dt = dt or datetime.now(timezone.utc)
    return f"{dt.year}-W{dt.isocalendar()[1]:02d}"


def main() -> None:
    week_id = get_week_id()
    print(f"[Routine A] 시작: {week_id}")

    gh = GitHubHelper()
    weekly_path = f"data/weekly/{week_id}"

    status = gh.read_json(f"{weekly_path}/status.json")
    if status and status.get("status") not in (None, "IDLE", "NEWS_SEARCHING"):
        print(f"[Routine A] 이미 진행 중: {status.get('status')} — 종료")
        return

    gh.write_json(f"{weekly_path}/status.json", {
        "week": week_id,
        "status": "NEWS_SEARCHING",
        "timeline": {"news_search_started": _now()},
    })

    # WebSearch로 검색된 기사를 수집 (Claude가 직접 호출)
    # 이 스크립트는 상태 관리와 저장만 담당
    # 실제 기사 데이터는 Routine A 지침의 Claude가 수집 후 직접 저장
    print("[Routine A] 검색 쿼리 준비 완료")
    for topic, cfg in TOPIC_QUERIES.items():
        print(f"  [{topic}] 해외: {cfg['foreign_query']}")
        print(f"  [{topic}] 국내: {cfg['domestic_query']}")

    print("[Routine A] Claude WebSearch로 기사 수집 후 저장 예정")


def save_articles_and_confirm(
    gh: GitHubHelper,
    week_id: str,
    articles: list[dict],
    status: dict | None = None,
) -> None:
    """Claude가 기사 수집 완료 후 호출하는 저장+자동확정 함수"""
    weekly_path = f"data/weekly/{week_id}"
    topics_covered = list({a["topic_tag"] for a in articles})

    candidates_data = {
        "week": week_id,
        "generated_at": _now(),
        "topics_covered": topics_covered,
        "total_count": len(articles),
        "articles": articles,
    }
    gh.write_json(f"{weekly_path}/news-candidates.json", candidates_data)

    # 자동 확정 — 관리자 검토 불필요
    gh.write_json(f"{weekly_path}/status.json", {
        "week": week_id,
        "status": "ARTICLES_CONFIRMED",
        "timeline": {
            "news_search_started": status.get("timeline", {}).get("news_search_started", _now()) if status else _now(),
            "news_search_completed": _now(),
            "articles_confirmed": _now(),
        },
        "topics_covered": topics_covered,
        "article_count": len(articles),
    })

    print(f"[Routine A] {len(articles)}건 저장 및 자동 확정 완료")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _build_notification_body(week_id: str, articles: list[dict]) -> str:
    lines = [
        f"이번 주({week_id}) AI 뉴스 {len(articles)}건이 자동 수집·확정되었습니다.",
        f"(해외 11건 + 국내 11건)",
        "",
        "토픽별 주요 기사:",
    ]
    topic_seen = set()
    for a in articles:
        if a["topic_tag"] not in topic_seen:
            topic_seen.add(a["topic_tag"])
            lines.append(f"  [{a['topic_tag']}] {a.get('title_ko') or a['title']}")
    lines.append("")
    lines.append("관리자 페이지에서 기획 주제를 입력해 주세요.")
    return "\n".join(lines)


if __name__ == "__main__":
    main()
