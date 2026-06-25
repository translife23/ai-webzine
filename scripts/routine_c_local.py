"""
Routine C 로컬 실행 버전 — PyGithub 프록시 차단 시 사용
로컬 파일에서 데이터 읽기 → HTML 빌드 → git commit/push → Gmail 발송
"""

import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from jinja2 import Environment, FileSystemLoader
from gmail_helper import send_newsletter, send_admin_notification

REPO_ROOT = Path(__file__).parent.parent
TEMPLATES_DIR = Path(__file__).parent / "templates"

TOPIC_COLORS: dict[str, str] = {
    "화폐금융":         "#1D4ED8",
    "금융투자":         "#1E40AF",
    "로봇":             "#065F46",
    "에너지":           "#92400E",
    "방산":             "#7F1D1D",
    "헬스케어·바이오":  "#0F766E",
    "반도체·HW인프라":  "#6B21A8",
    "농업·푸드테크":    "#166534",
    "제조·스마트팩토리":"#1E293B",
    "AI거버넌스·규제":  "#B45309",
    "항공우주·SAF":     "#1E3A8A",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_local_json(rel_path: str) -> dict | None:
    p = REPO_ROOT / rel_path
    if not p.exists():
        return None
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def _write_local_json(rel_path: str, data: dict) -> None:
    p = REPO_ROOT / rel_path
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _read_local_text(rel_path: str) -> str | None:
    p = REPO_ROOT / rel_path
    if not p.exists():
        return None
    return p.read_text(encoding="utf-8")


def _write_local_text(rel_path: str, text: str) -> None:
    p = REPO_ROOT / rel_path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def _git_commit_push(files: list[str], message: str) -> None:
    for f in files:
        subprocess.run(["git", "add", f], cwd=REPO_ROOT, check=True)
    result = subprocess.run(
        ["git", "commit", "-m", message],
        cwd=REPO_ROOT, capture_output=True, text=True
    )
    if result.returncode != 0 and "nothing to commit" not in result.stdout:
        raise RuntimeError(f"git commit 실패: {result.stderr}")
    push = subprocess.run(
        ["git", "push", "-u", "origin", "HEAD"],
        cwd=REPO_ROOT, capture_output=True, text=True
    )
    if push.returncode != 0:
        raise RuntimeError(f"git push 실패: {push.stderr}")
    print(f"[git] 커밋+푸시 완료: {message}")


def _md_to_html(md: str) -> str:
    lines = md.split("\n")
    out, in_ul = [], False
    for line in lines:
        if line.startswith("### "):
            if in_ul: out.append("</ul>"); in_ul = False
            out.append(f"<h3>{line[4:]}</h3>")
        elif line.startswith("## "):
            if in_ul: out.append("</ul>"); in_ul = False
            out.append(f"<h2>{line[3:]}</h2>")
        elif line.startswith("# "):
            if in_ul: out.append("</ul>"); in_ul = False
            out.append(f"<h1>{line[2:]}</h1>")
        elif re.match(r"^[-*] ", line):
            if not in_ul: out.append("<ul>"); in_ul = True
            item = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", line[2:])
            out.append(f"<li>{item}</li>")
        elif line.strip() == "":
            if in_ul: out.append("</ul>"); in_ul = False
            out.append("")
        else:
            if in_ul: out.append("</ul>"); in_ul = False
            line = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", line)
            line = re.sub(r"\*(.+?)\*", r"<em>\1</em>", line)
            out.append(f"<p>{line}</p>")
    if in_ul:
        out.append("</ul>")
    return "\n".join(out)


def _extract_title(md: str) -> str:
    for line in md.split("\n"):
        if line.startswith("# "):
            return line[2:].strip()
    return "AI 동향 기획 보고서"


def _extract_summary(md: str, max_chars: int = 200) -> str:
    for line in md.split("\n"):
        s = line.strip()
        if s and not s.startswith("#"):
            return s[:max_chars] + ("..." if len(s) > max_chars else "")
    return ""


def _find_week_to_publish() -> str | None:
    from datetime import timedelta
    now = datetime.now(timezone.utc)
    for offset in range(-1, 4):
        dt = now + timedelta(weeks=offset)
        wid = f"{dt.year}-W{dt.isocalendar()[1]:02d}"
        approval = _read_local_json(f"data/weekly/{wid}/approval.json")
        if not approval or not approval.get("approved"):
            continue
        status = _read_local_json(f"data/weekly/{wid}/status.json") or {}
        if status.get("status") == "PUBLISHED":
            continue
        return wid
    return None


def _build_webzine_html(week_id: str) -> tuple[str, str]:
    """웹진 HTML 빌드. (html, output_path) 반환."""
    weekly_path = f"data/weekly/{week_id}"
    articles_data = (
        _read_local_json(f"{weekly_path}/selected-articles.json")
        or _read_local_json(f"{weekly_path}/news-candidates.json")
        or {}
    )
    report_md = _read_local_text(f"{weekly_path}/draft-report.md") or ""

    articles: list[dict] = articles_data.get("articles", [])
    for a in articles:
        if "topic" not in a and "topic_tag" in a:
            a["topic"] = a["topic_tag"]
    if not articles:
        raise ValueError(f"선정된 기사 없음: {weekly_path}/selected-articles.json")
    if not report_md:
        raise ValueError(f"기획 보고서 없음: {weekly_path}/draft-report.md")

    report_title = _extract_title(report_md)
    report_html = _md_to_html(report_md)
    now = datetime.now(timezone.utc)
    pub_date = now.strftime("%Y년 %m월 %d일")
    year, wnum = week_id.split("-W")
    week_label = f"{year}년 제{int(wnum)}호"

    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)), autoescape=False)
    template = env.get_template("issue.html.j2")
    html = template.render(
        week_label=week_label,
        week_id=week_id,
        pub_date=pub_date,
        report_title=report_title,
        report_html=report_html,
        articles=articles,
        topic_colors=TOPIC_COLORS,
    )
    output_path = f"site/issues/{week_id}/index.html"
    _write_local_text(output_path, html)
    print(f"[Builder] 웹진 HTML 빌드 완료: {output_path}")
    return html, output_path


def _update_site_index(week_id: str, week_label: str, pub_date: str, report_title: str) -> str:
    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta http-equiv="refresh" content="0; url=issues/{week_id}/">
  <title>AI 웹진 — 정보시스템감리 AI 동향</title>
  <link rel="stylesheet" href="assets/css/webzine.css">
</head>
<body>
  <header class="site-header">
    <div class="container">
      <div class="header-inner">
        <div class="logo">
          <span class="logo-text">AI 웹진</span>
          <span class="logo-subtitle">정보시스템감리 AI 동향</span>
        </div>
        <div>
          <span class="issue-badge">{week_label}</span>
          <span class="pub-date">{pub_date}</span>
        </div>
      </div>
    </div>
  </header>
  <main class="container" style="padding-top:60px;text-align:center">
    <p style="font-size:18px;color:#64748B">최신 호로 이동 중...</p>
    <p style="margin-top:16px">
      <a href="issues/{week_id}/" style="color:#1A56DB">{week_label} — {report_title}</a>
    </p>
    <p style="margin-top:8px">
      <a href="archive/" style="color:#64748B;font-size:14px">전체 아카이브</a>
    </p>
  </main>
  <footer class="site-footer">
    <div class="container">
      <p>AI 웹진 · 정보시스템감리 AI 동향</p>
    </div>
  </footer>
</body>
</html>"""
    _write_local_text("site/index.html", html)
    return "site/index.html"


def _update_archive(week_id: str, week_label: str, pub_date: str, report_title: str) -> str | None:
    existing = _read_local_text("site/archive/index.html") or ""
    if week_id in existing:
        print(f"[Builder] 아카이브에 이미 {week_id} 존재 — 업데이트만")
        # Update the existing entry with new pub_date/report_title
        existing = re.sub(
            rf'(<div class="article-title"><a href="../issues/{re.escape(week_id)}/">)[^<]*(</a></div>\s*<div class="article-summary">)[^<]*(</div>\s*<div class="article-meta"><span>)[^<]*(</span>)',
            rf'\g<1>{week_label}\g<2>{report_title}\g<3>{pub_date}\g<4>',
            existing,
        )
        _write_local_text("site/archive/index.html", existing)
        return "site/archive/index.html"

    new_entry = (
        f'      <div class="article-card">\n'
        f'        <div class="article-title"><a href="../issues/{week_id}/">{week_label}</a></div>\n'
        f'        <div class="article-summary">{report_title}</div>\n'
        f'        <div class="article-meta"><span>{pub_date}</span></div>\n'
        f'      </div>'
    )
    if "아직 발행된 호가 없습니다" in existing:
        updated = existing.replace(
            '      <p style="color:#64748B">아직 발행된 호가 없습니다.</p>',
            new_entry,
        )
    else:
        updated = existing.replace(
            '    </div>\n  </main>',
            f'{new_entry}\n    </div>\n  </main>',
            1,
        )
    _write_local_text("site/archive/index.html", updated)
    return "site/archive/index.html"


def _build_newsletter_html(week_id: str) -> str:
    weekly_path = f"data/weekly/{week_id}"
    articles_data = (
        _read_local_json(f"{weekly_path}/selected-articles.json")
        or _read_local_json(f"{weekly_path}/news-candidates.json")
        or {}
    )
    report_md = _read_local_text(f"{weekly_path}/draft-report.md") or ""
    articles: list[dict] = articles_data.get("articles", [])
    for a in articles:
        if "topic" not in a and "topic_tag" in a:
            a["topic"] = a["topic_tag"]
    report_title = _extract_title(report_md)
    report_summary = _extract_summary(report_md, 150)

    now = datetime.now(timezone.utc)
    pub_date = now.strftime("%Y년 %m월 %d일")
    year, wnum = week_id.split("-W")
    week_label = f"{year}년 제{int(wnum)}호"

    articles_rows = ""
    for i in range(0, len(articles), 2):
        pair = articles[i:i+2]
        cells = ""
        for a in pair:
            color = TOPIC_COLORS.get(a.get("topic", ""), "#64748B")
            title = a.get("title_ko") or a.get("title", "")
            summary = (a.get("summary_ko") or a.get("summary", ""))[:100]
            origin = a.get("origin", "")
            origin_color = "#0EA5E9" if origin == "해외" else "#10B981"
            cells += f"""
              <td width="48%" style="vertical-align:top;padding:6px">
                <table width="100%" style="background:#fff;border:1px solid #E2E8F0;border-radius:8px">
                  <tr><td style="padding:14px">
                    <span style="display:inline-block;padding:2px 8px;border-radius:4px;background:{color};color:#fff;font-size:11px;font-weight:600">{a.get('topic','')}</span>
                    <span style="display:inline-block;padding:2px 8px;border-radius:4px;background:{origin_color};color:#fff;font-size:11px;font-weight:600;margin-left:4px">{origin}</span>
                    <div style="font-size:14px;font-weight:600;margin:8px 0 4px">
                      <a href="{a.get('url','#')}" style="color:#1A56DB;text-decoration:none">{title}</a>
                    </div>
                    <div style="font-size:12px;color:#64748B">{summary}...</div>
                    <div style="font-size:11px;color:#94A3B8;margin-top:6px">{a.get('source','')}</div>
                  </td></tr>
                </table>
              </td>"""
        if len(pair) == 1:
            cells += '<td width="48%"></td>'
        articles_rows += f"<tr>{cells}</tr>"

    repo = os.environ.get("GITHUB_REPO", "")
    owner = repo.split("/")[0] if "/" in repo else ""
    repo_name = repo.split("/")[1] if "/" in repo else repo
    webzine_url = f"https://{owner}.github.io/{repo_name}/issues/{week_id}/"

    return f"""<!DOCTYPE html>
<html lang="ko">
<head><meta charset="UTF-8"><title>AI 웹진 {week_label}</title></head>
<body style="margin:0;padding:0;background:#F8FAFC;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif">
<table width="100%" cellpadding="0" cellspacing="0">
  <tr><td align="center" style="padding:24px 16px">
    <table width="600" cellpadding="0" cellspacing="0" style="max-width:600px">
      <tr>
        <td style="background:#1A56DB;padding:28px 24px;border-radius:12px 12px 0 0">
          <div style="color:#fff;font-size:22px;font-weight:800">AI 웹진</div>
          <div style="color:#93C5FD;font-size:13px;margin-top:4px">{week_label} · {pub_date}</div>
        </td>
      </tr>
      <tr>
        <td style="background:#EFF6FF;padding:20px 24px;border-left:1px solid #E2E8F0;border-right:1px solid #E2E8F0">
          <div style="font-size:11px;font-weight:700;color:#1A56DB;letter-spacing:1px;margin-bottom:10px">이번 주 기획 보고서</div>
          <div style="background:#fff;border:1px solid #BFDBFE;border-radius:8px;padding:16px">
            <div style="font-size:15px;font-weight:700;color:#1E293B;margin-bottom:6px">{report_title}</div>
            <div style="font-size:13px;color:#64748B">{report_summary}</div>
          </div>
          <div style="margin-top:12px;text-align:center">
            <a href="{webzine_url}" style="display:inline-block;padding:10px 24px;background:#1A56DB;color:#fff;border-radius:6px;font-size:13px;font-weight:600;text-decoration:none">웹진 전문 보기 →</a>
          </div>
        </td>
      </tr>
      <tr>
        <td style="background:#fff;padding:20px 24px;border-left:1px solid #E2E8F0;border-right:1px solid #E2E8F0">
          <div style="font-size:11px;font-weight:700;color:#64748B;letter-spacing:1px;margin-bottom:14px">이번 주 AI 동향 뉴스</div>
          <table width="100%" cellspacing="0">
            {articles_rows}
          </table>
        </td>
      </tr>
      <tr>
        <td style="background:#1E293B;padding:20px 24px;border-radius:0 0 12px 12px;text-align:center">
          <p style="color:#94A3B8;font-size:12px;margin:0">
            AI 웹진 · 정보시스템감리 AI 동향
          </p>
        </td>
      </tr>
    </table>
  </td></tr>
</table>
</body>
</html>"""


def main() -> None:
    week_id = _find_week_to_publish()
    if not week_id:
        print("[Routine C] 발행 대기 중인 승인 주차 없음 — 종료")
        return

    print(f"[Routine C] 발행 시작: {week_id}")
    weekly_path = f"data/weekly/{week_id}"
    status = _read_local_json(f"{weekly_path}/status.json") or {}

    # 상태: PUBLISHING
    _write_local_json(f"{weekly_path}/status.json", {
        **status,
        "status": "PUBLISHING",
        "timeline": {**status.get("timeline", {}), "publishing_started": _now()},
    })
    _git_commit_push(
        [str(REPO_ROOT / weekly_path / "status.json")],
        f"auto: {week_id} 발행 시작 (PUBLISHING)"
    )

    # 웹진 HTML 빌드
    print("[Routine C] 웹진 빌드 중...")
    try:
        _, output_path = _build_webzine_html(week_id)
        articles_data = (
            _read_local_json(f"{weekly_path}/selected-articles.json") or {}
        )
        report_md = _read_local_text(f"{weekly_path}/draft-report.md") or ""
        report_title = _extract_title(report_md)
        now = datetime.now(timezone.utc)
        pub_date = now.strftime("%Y년 %m월 %d일")
        year, wnum = week_id.split("-W")
        week_label = f"{year}년 제{int(wnum)}호"

        index_path = _update_site_index(week_id, week_label, pub_date, report_title)
        archive_path = _update_archive(week_id, week_label, pub_date, report_title)

        files_to_commit = [
            str(REPO_ROOT / output_path),
            str(REPO_ROOT / index_path),
        ]
        if archive_path:
            files_to_commit.append(str(REPO_ROOT / archive_path))

        _git_commit_push(files_to_commit, f"site: {week_label} 웹진 빌드")
        print("[Routine C] 웹진 빌드 완료 → GitHub Pages 배포 시작됨")
    except Exception as exc:
        print(f"[Routine C] 웹진 빌드 실패: {exc} — 뉴스레터 발송 중단")
        _write_local_json(f"{weekly_path}/status.json", {
            **status,
            "status": "PUBLISH_FAILED",
            "error": str(exc),
            "timeline": {**status.get("timeline", {}), "failed": _now()},
        })
        _git_commit_push(
            [str(REPO_ROOT / weekly_path / "status.json")],
            f"auto: {week_id} 발행 실패"
        )
        return

    # 뉴스레터 HTML
    newsletter_html = _read_local_text(f"{weekly_path}/draft-newsletter.html") or ""
    if not newsletter_html:
        print("[Routine C] draft-newsletter.html 없음 → 뉴스레터 HTML 자동 생성")
        newsletter_html = _build_newsletter_html(week_id)

    # 수신자 목록
    recipients_data = _read_local_json("data/recipients.json") or {}
    active_recipients = [
        r["email"]
        for r in recipients_data.get("recipients", [])
        if r.get("active", True)
    ]

    # 뉴스레터 발송
    year, wnum = week_id.split("-W")
    week_label = f"{year}년 제{int(wnum)}호"
    now_dt = datetime.now(timezone.utc)
    date_str = now_dt.strftime("%Y년 %m월")
    subject = f"[AI 웹진 {week_label}] 이번 주 AI 동향 — {date_str}"

    result = {"sent": [], "failed": []}
    if active_recipients and newsletter_html:
        print(f"[Routine C] 뉴스레터 {len(active_recipients)}명 발송 중...")
        result = send_newsletter(active_recipients, subject, newsletter_html)
        print(f"[Routine C] 발송 완료: 성공 {len(result['sent'])}명, 실패 {len(result['failed'])}명")
    else:
        print("[Routine C] 수신자 없거나 뉴스레터 없음 — 발송 건너뜀")

    # 상태 PUBLISHED
    _write_local_json(f"{weekly_path}/status.json", {
        **status,
        "status": "PUBLISHED",
        "timeline": {
            **status.get("timeline", {}),
            "publishing_started": status.get("timeline", {}).get("publishing_started", _now()),
            "published": _now(),
        },
        "newsletter_sent": len(result["sent"]),
        "newsletter_failed": len(result["failed"]),
        "webzine_build": "github_pages",
        "webzine_url": f"https://translife23.github.io/ai-webzine/issues/{week_id}/",
    })
    _git_commit_push(
        [str(REPO_ROOT / weekly_path / "status.json")],
        f"auto: {week_id} 발행 완료 (PUBLISHED)"
    )

    # 관리자 알림
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


if __name__ == "__main__":
    main()
