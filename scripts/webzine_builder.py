"""
웹진 빌더 — Jinja2 템플릿으로 site/ 디렉토리에 정적 HTML을 빌드한다.

참고 디자인:
- 웹진 레이아웃: https://webzine.nrf.re.kr/magazine/2503/index.php
- 뉴스레터 형식: https://maily.so
"""

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from github_helper import GitHubHelper


SITE_DIR = Path(__file__).parent.parent / "site"
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


def _get_issue_number(week_id: str) -> int:
    """YYYY-WNN → 대략적인 호수 계산 (2026-W01 = 1호)"""
    try:
        year, week = week_id.split("-W")
        return (int(year) - 2026) * 52 + int(week)
    except Exception:
        return 1


def build_webzine(week_id: str, candidates: dict, tech_report: str, nontech_report: str) -> str:
    """
    웹진 HTML을 빌드하여 문자열로 반환한다.
    GitHub 저장소의 site/issues/{week_id}/index.html 에 저장된다.
    """
    issue_num = _get_issue_number(week_id)
    selected = candidates.get("selected", [])
    topics_covered = candidates.get("topics_covered", [])

    # 토픽별로 기사 그룹화
    topic_groups: dict[str, list[dict]] = {}
    for article in selected:
        tag = article["topic_tag"]
        topic_groups.setdefault(tag, []).append(article)

    pub_date = datetime.now(timezone.utc).strftime("%Y년 %m월 %d일")

    html = _render_webzine_html(
        week_id=week_id,
        issue_num=issue_num,
        pub_date=pub_date,
        tech_report_md=tech_report,
        nontech_report_md=nontech_report,
        articles=selected,
        topic_groups=topic_groups,
        topics_covered=topics_covered,
    )
    return html


def build_newsletter_html(
    week_id: str,
    candidates: dict,
    tech_report: str,
    nontech_report: str,
    intro_text: str,
) -> str:
    """이메일용 뉴스레터 HTML을 빌드하여 문자열로 반환한다."""
    issue_num = _get_issue_number(week_id)
    selected = candidates.get("selected", [])
    pub_date = datetime.now(timezone.utc).strftime("%Y년 %m월 %d일")

    # 기획 보고서 요약 (첫 300자)
    tech_summary = _extract_summary(tech_report)
    nontech_summary = _extract_summary(nontech_report)
    tech_title = _extract_title(tech_report)
    nontech_title = _extract_title(nontech_report)

    return _render_newsletter_html(
        week_id=week_id,
        issue_num=issue_num,
        pub_date=pub_date,
        intro_text=intro_text,
        tech_title=tech_title,
        tech_summary=tech_summary,
        nontech_title=nontech_title,
        nontech_summary=nontech_summary,
        articles=selected,
    )


def _extract_title(md: str) -> str:
    match = re.search(r"^# (.+)", md, re.MULTILINE)
    return match.group(1).strip() if match else "기획 보고서"


def _extract_summary(md: str, max_chars: int = 200) -> str:
    lines = [l.strip() for l in md.split("\n") if l.strip() and not l.startswith("#")]
    text = " ".join(lines)
    return text[:max_chars] + "..." if len(text) > max_chars else text


# ─── 웹진 HTML 템플릿 ──────────────────────────────────────────────────────────

_TOPIC_COLORS = {
    "화폐금융":         "#2563EB",
    "금융투자":         "#7C3AED",
    "로봇":             "#DC2626",
    "에너지":           "#D97706",
    "방산":             "#0F766E",
    "헬스케어·바이오":  "#BE185D",
    "반도체·HW인프라":  "#1D4ED8",
    "농업·푸드테크":    "#15803D",
    "제조·스마트팩토리":"#9333EA",
    "AI거버넌스·규제":  "#B45309",
    "항공우주·SAF":     "#0369A1",
}


def _topic_color(tag: str) -> str:
    return _TOPIC_COLORS.get(tag, "#64748B")


def _md_to_html(md: str) -> str:
    """기본적인 Markdown → HTML 변환 (h1~h3, 굵게, 단락)."""
    lines = md.split("\n")
    html_lines = []
    for line in lines:
        if line.startswith("### "):
            html_lines.append(f"<h3>{line[4:]}</h3>")
        elif line.startswith("## "):
            html_lines.append(f"<h2>{line[3:]}</h2>")
        elif line.startswith("# "):
            html_lines.append(f"<h1>{line[2:]}</h1>")
        elif line.strip().startswith("- ") or line.strip().startswith("* "):
            html_lines.append(f"<li>{line.strip()[2:]}</li>")
        elif line.strip() == "":
            html_lines.append("<br>")
        else:
            line = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", line)
            html_lines.append(f"<p>{line}</p>")
    return "\n".join(html_lines)


def _render_webzine_html(
    week_id, issue_num, pub_date, tech_report_md, nontech_report_md,
    articles, topic_groups, topics_covered
) -> str:
    tech_html = _md_to_html(tech_report_md)
    nontech_html = _md_to_html(nontech_report_md)
    tech_title = _extract_title(tech_report_md)
    nontech_title = _extract_title(nontech_report_md)

    articles_html = ""
    for article in articles:
        color = _topic_color(article["topic_tag"])
        articles_html += f"""
        <div class="article-card">
          <span class="topic-tag" style="background:{color}">{article['topic_tag']}</span>
          <h3 class="article-title">
            <a href="{article['url']}" target="_blank" rel="noopener">{article['title']}</a>
          </h3>
          <p class="article-summary">{article.get('summary','')}</p>
          <div class="article-meta">
            <span>{article.get('source','')}</span>
            <span>{article.get('published_date','')}</span>
          </div>
        </div>"""

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AI 웹진 제{issue_num}호 — {week_id}</title>
  <link rel="stylesheet" href="../../assets/css/webzine.css">
</head>
<body>
  <header class="site-header">
    <div class="container">
      <div class="header-inner">
        <div class="logo">
          <span class="logo-text">AI 웹진</span>
          <span class="logo-subtitle">정보시스템감리 AI 동향</span>
        </div>
        <div class="issue-meta">
          <span class="issue-badge">제{issue_num}호</span>
          <span class="pub-date">{pub_date}</span>
        </div>
      </div>
    </div>
  </header>

  <main class="container">

    <!-- 기획 보고서 1: 기술 -->
    <section class="report-section">
      <div class="section-label">기획 보고서 · 기술 분야</div>
      <div class="report-card">
        <h2 class="report-title">{tech_title}</h2>
        <details>
          <summary>전문 보기</summary>
          <div class="report-body">{tech_html}</div>
        </details>
      </div>
    </section>

    <!-- 기획 보고서 2: 비기술 -->
    <section class="report-section">
      <div class="section-label">기획 보고서 · 비기술 분야</div>
      <div class="report-card">
        <h2 class="report-title">{nontech_title}</h2>
        <details>
          <summary>전문 보기</summary>
          <div class="report-body">{nontech_html}</div>
        </details>
      </div>
    </section>

    <!-- 주요 뉴스 12선 -->
    <section class="news-section">
      <div class="section-label">이번 주 AI 주요 뉴스 12선</div>
      <div class="articles-grid">
        {articles_html}
      </div>
    </section>

  </main>

  <footer class="site-footer">
    <div class="container">
      <p>AI 웹진은 정보시스템 감리 종사자를 위한 주간 AI 동향 채널입니다.</p>
      <p><a href="../../archive/">전체 아카이브 보기</a></p>
    </div>
  </footer>

  <script src="../../assets/js/webzine.js"></script>
</body>
</html>"""


def _render_newsletter_html(
    week_id, issue_num, pub_date, intro_text,
    tech_title, tech_summary, nontech_title, nontech_summary, articles
) -> str:
    articles_html = ""
    for i, article in enumerate(articles):
        color = _topic_color(article["topic_tag"])
        articles_html += f"""
        <tr>
          <td style="padding:8px;vertical-align:top;width:50%">
            <table width="100%" cellpadding="12" style="background:#fff;border:1px solid #E2E8F0;border-radius:8px">
              <tr>
                <td>
                  <span style="display:inline-block;padding:2px 8px;border-radius:4px;background:{color};color:#fff;font-size:11px;font-weight:600;margin-bottom:8px">{article['topic_tag']}</span><br>
                  <strong><a href="{article['url']}" style="color:#1A56DB;text-decoration:none;font-size:14px">{article['title']}</a></strong><br>
                  <p style="color:#64748B;font-size:13px;margin:6px 0">{article.get('summary','')[:100]}...</p>
                  <span style="color:#94A3B8;font-size:12px">{article.get('source','')} · {article.get('published_date','')}</span>
                </td>
              </tr>
            </table>
          </td>
          {"<td></td>" if i % 2 == 0 and i == len(articles)-1 else ""}
        </tr>""" if i % 2 == 0 else f"""
          <td style="padding:8px;vertical-align:top;width:50%">
            <table width="100%" cellpadding="12" style="background:#fff;border:1px solid #E2E8F0;border-radius:8px">
              <tr>
                <td>
                  <span style="display:inline-block;padding:2px 8px;border-radius:4px;background:{color};color:#fff;font-size:11px;font-weight:600;margin-bottom:8px">{article['topic_tag']}</span><br>
                  <strong><a href="{article['url']}" style="color:#1A56DB;text-decoration:none;font-size:14px">{article['title']}</a></strong><br>
                  <p style="color:#64748B;font-size:13px;margin:6px 0">{article.get('summary','')[:100]}...</p>
                  <span style="color:#94A3B8;font-size:12px">{article.get('source','')} · {article.get('published_date','')}</span>
                </td>
              </tr>
            </table>
          </td>
        </tr>"""

    return f"""<!DOCTYPE html>
<html lang="ko">
<head><meta charset="UTF-8"><title>AI 웹진 제{issue_num}호</title></head>
<body style="margin:0;padding:0;background:#F8FAFC;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif">
<table width="100%" cellpadding="0" cellspacing="0">
  <tr><td align="center" style="padding:24px 16px">
    <table width="600" cellpadding="0" cellspacing="0" style="max-width:600px">

      <!-- 헤더 -->
      <tr>
        <td style="background:#1A56DB;padding:32px 24px;border-radius:12px 12px 0 0">
          <div style="color:#fff;font-size:22px;font-weight:700">AI 웹진</div>
          <div style="color:#93C5FD;font-size:14px;margin-top:4px">제{issue_num}호 · {pub_date}</div>
        </td>
      </tr>

      <!-- 인트로 -->
      <tr>
        <td style="background:#fff;padding:24px;border-left:1px solid #E2E8F0;border-right:1px solid #E2E8F0">
          <p style="color:#1E293B;font-size:15px;line-height:1.7;margin:0">{intro_text}</p>
        </td>
      </tr>

      <!-- 기획 보고서 -->
      <tr>
        <td style="background:#EFF6FF;padding:20px 24px;border-left:1px solid #E2E8F0;border-right:1px solid #E2E8F0">
          <div style="font-size:12px;font-weight:600;color:#1A56DB;text-transform:uppercase;letter-spacing:1px;margin-bottom:12px">이번 주 기획 보고서</div>
          <table width="100%">
            <tr>
              <td width="48%" style="background:#fff;padding:16px;border-radius:8px;border:1px solid #BFDBFE;vertical-align:top">
                <div style="font-size:11px;color:#1A56DB;font-weight:600;margin-bottom:6px">기술 분야</div>
                <div style="font-size:14px;font-weight:600;color:#1E293B;margin-bottom:8px">{tech_title}</div>
                <div style="font-size:13px;color:#64748B">{tech_summary[:120]}...</div>
              </td>
              <td width="4%"></td>
              <td width="48%" style="background:#fff;padding:16px;border-radius:8px;border:1px solid #BFDBFE;vertical-align:top">
                <div style="font-size:11px;color:#7C3AED;font-weight:600;margin-bottom:6px">비기술 분야</div>
                <div style="font-size:14px;font-weight:600;color:#1E293B;margin-bottom:8px">{nontech_title}</div>
                <div style="font-size:13px;color:#64748B">{nontech_summary[:120]}...</div>
              </td>
            </tr>
          </table>
        </td>
      </tr>

      <!-- 뉴스 12선 -->
      <tr>
        <td style="background:#fff;padding:20px 24px;border-left:1px solid #E2E8F0;border-right:1px solid #E2E8F0">
          <div style="font-size:12px;font-weight:600;color:#64748B;text-transform:uppercase;letter-spacing:1px;margin-bottom:16px">이번 주 AI 주요 뉴스 12선</div>
          <table width="100%" cellspacing="0">
            {articles_html}
          </table>
        </td>
      </tr>

      <!-- 푸터 -->
      <tr>
        <td style="background:#1E293B;padding:20px 24px;border-radius:0 0 12px 12px;text-align:center">
          <p style="color:#94A3B8;font-size:12px;margin:0">
            AI 웹진 · 정보시스템감리 AI 동향<br>
            <a href="{{webzine_url}}" style="color:#60A5FA">웹진 전문 보기</a> &nbsp;|&nbsp;
            <a href="{{unsubscribe_url}}" style="color:#60A5FA">구독 취소</a>
          </p>
        </td>
      </tr>

    </table>
  </td></tr>
</table>
</body>
</html>"""
