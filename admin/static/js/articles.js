/* 기사 검토 탭 — 토픽당 해외 1건 + 국내 1건 표시, 확정 버튼 없음 */
const TOPIC_COLORS = {
  "화폐금융":"#2563EB","금융투자":"#7C3AED","로봇":"#DC2626","에너지":"#D97706",
  "방산":"#0F766E","헬스케어·바이오":"#BE185D","반도체·HW인프라":"#1D4ED8",
  "농업·푸드테크":"#15803D","제조·스마트팩토리":"#9333EA","AI거버넌스·규제":"#B45309","항공우주·SAF":"#0369A1"
};

async function loadArticles() {
  const el = document.getElementById("tab-articles");
  el.innerHTML = `<h2 class="page-title">기사 검토</h2><p class="text-muted">불러오는 중...</p>`;
  try {
    const data = await API.get("/workflow/articles");
    const articles = data.articles || data.selected || [];

    if (!articles.length) {
      el.innerHTML = `<h2 class="page-title">기사 검토</h2><p class="text-muted">수집된 기사가 없습니다. Routine A 실행 후 확인하세요.</p>`;
      return;
    }

    // 토픽별 그룹화
    const byTopic = {};
    for (const a of articles) {
      if (!byTopic[a.topic_tag]) byTopic[a.topic_tag] = [];
      byTopic[a.topic_tag].push(a);
    }

    const renderCard = (a) => {
      const color = TOPIC_COLORS[a.topic_tag] || "#64748B";
      const originBadge = a.origin === "국내"
        ? `<span style="font-size:10px;background:#dcfce7;color:#166534;border-radius:4px;padding:2px 6px;margin-left:6px">국내</span>`
        : `<span style="font-size:10px;background:#dbeafe;color:#1e40af;border-radius:4px;padding:2px 6px;margin-left:6px">해외</span>`;
      return `<div class="article-card" data-url="${escHtml(a.url)}">
        <div style="display:flex;align-items:center;margin-bottom:8px">
          <span class="topic-badge" style="background:${color}">${escHtml(a.topic_tag)}</span>
          ${originBadge}
        </div>
        <div class="article-title-text">${escHtml(a.title_ko || a.title)}</div>
        <div class="article-meta-text">${escHtml(a.source)} · ${escHtml(a.published_date)}</div>
        <div class="article-meta-text text-muted" style="margin-top:6px;font-size:12px">${escHtml(((a.summary_ko || a.summary)||"").slice(0,80))}...</div>
        <a href="${escHtml(a.url)}" target="_blank" style="font-size:12px;color:#1A56DB;display:block;margin-top:6px">원문 보기 →</a>
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
