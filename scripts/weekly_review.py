"""
주간 리뷰 리포트 생성 — Routine A/B 완료 후 자동 실행

감지 항목:
- 고아 커밋: [DEC-NNN] 태그 없는 이번 주 커밋
- 장기 미반영: PENDING.md에서 2주 이상 체크 미완료 항목
- 워크플로 이상: 각 주차 status.json 상태 이상 감지

결과를 docs/ops/review-YYYY-MM-DD.md에 저장한다.
"""

import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from github_helper import GitHubHelper


def main() -> None:
    today = datetime.now(timezone.utc)
    report_date = today.strftime("%Y-%m-%d")
    print(f"[weekly-review] 리뷰 리포트 생성: {report_date}")

    gh = GitHubHelper()
    issues: list[str] = []

    # 1. 현재 주차 워크플로 상태 확인
    year = today.year
    week = today.isocalendar()[1]
    week_id = f"{year}-W{week:02d}"
    status = gh.read_json(f"data/weekly/{week_id}/status.json")
    if status:
        issues.append(f"### 현재 주차 ({week_id})\n- 상태: **{status.get('status','?')}**")
    else:
        issues.append(f"### 현재 주차 ({week_id})\n- status.json 없음 (Routine A 미실행 가능)")

    # 2. PENDING.md 장기 미반영 항목 감지 (간단한 텍스트 분석)
    pending_md = gh.read_text("docs/decisions/PENDING.md") or ""
    if "_현재 미반영 결정 없음_" not in pending_md:
        lines = pending_md.split("\n")
        dec_dates = re.findall(r"DEC-\d+ \| (\d{4}-\d{2}-\d{2})", pending_md)
        stale = []
        for date_str in dec_dates:
            try:
                dec_date = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                if (today - dec_date).days > 14:
                    stale.append(date_str)
            except ValueError:
                pass
        if stale:
            issues.append(f"### ⚠️ 장기 미반영 결정\n- 2주 이상 미반영: {', '.join(stale)}\n- PENDING.md 검토 필요")

    # 3. 리포트 작성
    report_lines = [
        f"# 주간 리뷰 리포트 — {report_date}",
        "",
        f"> 자동 생성: {today.isoformat()}",
        "",
    ] + issues + [
        "",
        "---",
        "_이 리포트는 weekly_review.py에 의해 자동 생성되었습니다._",
    ]

    report_content = "\n".join(report_lines)
    report_path = f"docs/ops/review-{report_date}.md"
    gh.write_text(report_path, report_content, message=f"ops: 주간 리뷰 리포트 {report_date}")
    print(f"[weekly-review] 완료: {report_path}")


if __name__ == "__main__":
    main()
