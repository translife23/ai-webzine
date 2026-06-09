/* 기사 검토 탭 — 토픽당 해외 1건 + 국내 1건, 요약 4문장 표시 */
const TOPIC_COLORS = {
  "화폐금융":"#2563EB","금융투자":"#7C3AED","로봇":"#DC2626","에너지":"#D97706",
  "방산":"#0F766E","헬스케어·바이오":"#BE185D","반도체·HW인프라":"#1D4ED8",
  "농업·푸드테크":"#15803D","제조·스마트팩토리":"#9333EA","AI거버넌스·규제":"#B45309","항공우주·SAF":"#0369A1"
};

function summaryBullets(text) {
  if (!text) return "";
  // 마침표/다. 기준으로 문장 분리
  const raw = text.trim();
  const parts = raw.split(/(?<=다\.)\s+|(?<=[\.！？])\s+/).filter(s => s.trim().length > 8);
  let bullets = parts.slice(0, 4).map(s => {
    s = s.trim().replace(/\.$/, "");
    return s.length > 45 ? s.slice(0, 43) + "…" : s;
  });
  // 문장 분리가 안 됐을 경우 40자씩 청크
  if (bullets.length < 2) {
    bullets = [];
    for (let i = 0; i < raw.length && bullets.length < 4; i += 40) {
      bullets.push(raw.slice(i, i + 40).trim());
    }
  }
  return `<ul style="margin:6px 0 0 16px;padding:0;list-style:disc">${
    bullets.map(b => `<li style="font-size:12px;color:#475569;line-height:1.5;margin-bottom:3px">${escHtml(b)}</li>`).join("")
  }</ul>`;
}

async function loadArticles() {
  const el = document.getElementById("tab-articles");
  el.innerHTML = `<h2 class="page-title">기사 검토</h2><p class="text-muted">불러오는 중...</p>`;
  try {
    // 발행 완료 상태면 기사 목록 대신 완료 메시지 표시
    const status = await API.get("/workflow/status");
    if (status.status === "PUBLISHED") {
      el.innerHTML = `<h2 class="page-title">기사 검토</h2>
        <div class="card"><p class="text-muted">✅ 이번 주(${escHtml(status.week)}) 웹진 발행이 완료되었습니다.</p></div>`;
      return;
    }

    const data = await API.get("/workflow/articles");
    const articles = data.articles || data.selected || [];

    if (!articles.length) {
      el.innerHTML = `<h2 class="page-title">기사 검토</h2>
        <div class="card"><p class="text-muted">수집된 기사가 없습니다. Routine A 실행 후 확인하세요.</p></div>`;
      return;
    }

    // 토픽별 그룹화
    const byTopic = {};
    for (const a of articles) {
      const key = a.topic || a.topic_tag || "기타";
      if (!byTopic[key]) byTopic[key] = [];
      byTopic[key].push(a);
    }

    const renderCard = (a) => {
      const color = TOPIC_COLORS[a.topic || a.topic_tag] || "#64748B";
      const originBadge = a.origin === "국내"
        ? `<span style="font-size:10px;background:#dcfce7;color:#166534;border-radius:4px;padding:2px 6px;margin-left:6px">국내</span>`
        : `<span style="font-size:10px;background:#dbeafe;color:#1e40af;border-radius:4px;padding:2px 6px;margin-left:6px">해외</span>`;
      const summary = a.summary_ko || a.summary || "";
      return `<div class="article-card">
        <div style="display:flex;align-items:center;margin-bottom:8px">
          <span class="topic-badge" style="background:${color}">${escHtml(a.topic || a.topic_tag)}</span>
          ${originBadge}
        </div>
        <div class="article-title-text">
          <a href="${escHtml(a.url)}" target="_blank" style="color:inherit;text-decoration:none">${escHtml(a.title_ko || a.title)}</a>
        </div>
        <div class="article-meta-text" style="margin-bottom:4px">${escHtml(a.source)} · ${escHtml(a.published_date || "")}</div>
        ${summaryBullets(summary)}
      </div>`;
    };

    const topicSections = Object.entries(byTopic).map(([topic, arts]) => `
      <div style="margin-bottom:24px">
        <div style="font-weight:600;font-size:14px;color:#374151;margin-bottom:8px;padding-bottom:4px;border-bottom:2px solid ${TOPIC_COLORS[topic]||'#e5e7eb'}">${escHtml(topic)}</div>
        <div class="article-grid">${arts.map(a => renderCard(a)).join("")}</div>
      </div>
    `).join("");

    el.innerHTML = `
      <h2 class="page-title">기사 검토</h2>
      <div class="card">
        <div class="card-title">수집 기사 (${articles.length}건) — 해외 ${articles.filter(a=>a.origin==="해외").length}건 + 국내 ${articles.filter(a=>a.origin==="국내").length}건</div>
        <div class="text-muted text-sm" style="margin-bottom:16px">커버 토픽: ${escHtml((data.topics_covered||[]).join(", "))}</div>
        ${topicSections}
      </div>`;

  } catch (err) {
    el.innerHTML = `<h2 class="page-title">기사 검토</h2><p class="text-muted">${escHtml(err.message)}</p>`;
  }
}
