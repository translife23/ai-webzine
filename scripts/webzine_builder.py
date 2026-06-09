"""
웹진 빌더 — GitHub 데이터로 site/issues/YYYY-WNN/index.html 생성 후 커밋
"""

import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from jinja2 import Environment, FileSystemLoader
from github_helper import GitHubHelper

TEMPLATES_DIR = Path(__file__).parent / "templates"

TOPIC_COLORS: dict[str, str] = {
    "화폐금융":        "#1D4ED8",
    "금융투자":        "#1E40AF",
    "로봇":            "#065F46",
    "에너지":          "#92400E",
    "방산":            "#7F1D1D",
    "헬스케어·바이오": "#0F766E",
    "반도체·HW인프라": "#6B21A8",
    "농업·푸드테크":   "#166534",
    "제조·스마트팩토리":"#1E293B",
    "AI거버넌스·규제": "#B45309",
    "항공우주·SAF":    "#1E3A8A",
}


def md_to_html(md: str) -> str:
    """마크다운 → HTML 변환 (외부 라이브러리 없이)"""
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


def extract_title(md: str) -> str:
    """보고서 마크다운에서 첫 번째 # 제목 추출"""
    for line in md.split("\n"):
        if line.startswith("# "):
            return line[2:].strip()
    return "AI 동향 기획 보고서"


def extract_summary(md: str, max_chars: int = 200) -> str:
    """보고서 첫 본문 단락 추출 (요약용)"""
    for line in md.split("\n"):
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            return stripped[:max_chars] + ("..." if len(stripped) > max_chars else "")
    return ""


def build(week_id: str | None = None) -> str:
    """
    웹진 HTML을 빌드하여 GitHub에 커밋한다.

    Returns:
        생성된 파일 경로 (site/issues/YYYY-WNN/index.html)
    """
    gh = GitHubHelper()

    if week_id is None:
        now = datetime.now(timezone.utc)
        week_id = f"{now.year}-W{now.isocalendar()[1]:02d}"

    weekly_path = f"data/weekly/{week_id}"

    articles_data = (
        gh.read_json(f"{weekly_path}/selected-articles.json")
        or gh.read_json(f"{weekly_path}/news-candidates.json")
        or {}
    )
    report_md = gh.read_text(f"{weekly_path}/draft-report.md") or ""

    articles: list[dict] = articles_data.get("articles", [])
    for a in articles:
        if "topic" not in a and "topic_tag" in a:
            a["topic"] = a["topic_tag"]
    if not articles:
        raise ValueError(f"선정된 기사가 없습니다: {weekly_path}/selected-articles.json")
    if not report_md:
        raise ValueError(f"기획 보고서가 없습니다: {weekly_path}/draft-report.md")

    report_title = extract_title(report_md)
    report_html = md_to_html(report_md)
    report_summary = extract_summary(report_md)

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
    gh.write_text(output_path, html, f"site: {week_label} 웹진 빌드")

    _update_site_index(gh, week_id, week_label, pub_date, report_title)
    _update_archive(gh, week_id, week_label, pub_date, report_title)

    print(f"[Builder] 빌드 완료: {output_path}")
    return output_path


def build_newsletter_html(week_id: str) -> str:
    """
    이메일용 뉴스레터 HTML을 빌드하여 반환한다.
    """
    gh = GitHubHelper()
    weekly_path = f"data/weekly/{week_id}"

    articles_data = (
        gh.read_json(f"{weekly_path}/selected-articles.json")
        or gh.read_json(f"{weekly_path}/news-candidates.json")
        or {}
    )
    report_md = gh.read_text(f"{weekly_path}/draft-report.md") or ""

    articles: list[dict] = articles_data.get("articles", [])
    for a in articles:
        if "topic" not in a and "topic_tag" in a:
            a["topic"] = a["topic_tag"]
    report_title = extract_title(report_md)
    report_summary = extract_summary(report_md, 150)

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


def _update_site_index(gh: GitHubHelper, week_id: str, week_label: str,
                       pub_date: str, report_title: str) -> None:
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
    gh.write_text("site/index.html", html, f"site: index.html → {week_label}")


def _update_archive(gh: GitHubHelper, week_id: str, week_label: str,
                    pub_date: str, report_title: str) -> None:
    existing = gh.read_text("site/archive/index.html") or ""
    if week_id in existing:
        return

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

    gh.write_text("site/archive/index.html", updated, f"site: archive에 {week_label} 추가")


if __name__ == "__main__":
    week = sys.argv[1] if len(sys.argv) > 1 else None
    build(week)
