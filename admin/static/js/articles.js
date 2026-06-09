/* 기사 검토 탭 */
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
    const selected = data.selected || [];
    const spare = data.spare || [];

    const renderCard = (a, isSpare) => {
      const color = TOPIC_COLORS[a.topic_tag] || "#64748B";
      return `<div class="article-card${isSpare ? " spare" : ""}" data-url="${escHtml(a.url)}">
        <span class="topic-badge" style="background:${color}">${escHtml(a.topic_tag)}</span>
        <div class="article-title-text">${escHtml(a.title_ko || a.title)}</div>
        <div class="article-meta-text">${escHtml(a.source)} · ${escHtml(a.published_date)}</div>
        <div class="article-meta-text text-muted" style="margin-top:6px;font-size:12px">${escHtml(((a.summary_ko || a.summary)||"").slice(0,80))}...</div>
        <a href="${escHtml(a.url)}" target="_blank" style="font-size:12px;color:#1A56DB;display:block;margin-top:6px">원문 보기 →</a>
      </div>`;
    };

    el.innerHTML = `
      <h2 class="page-title">기사 검토</h2>
      <div class="card">
        <div class="flex-between">
          <div>
            <div class="card-title">선정 기사 (${selected.length}건)</div>
            <div class="text-muted text-sm">커버 토픽: ${escHtml((data.topics_covered||[]).join(", "))}</div>
          </div>
          <button class="btn btn-success" id="confirm-articles-btn">선정 확정</button>
        </div>
        <div class="article-grid mt-16">${selected.map(a => renderCard(a, false)).join("")}</div>
      </div>
      ${spare.length ? `
      <div class="card">
        <div class="card-title">여분 기사 (${spare.length}건) — 위 기사와 교체 가능</div>
        <div class="article-grid">${spare.map(a => renderCard(a, true)).join("")}</div>
      </div>` : ""}`;

    document.getElementById("confirm-articles-btn").addEventListener("click", async () => {
      if (!confirm("선정된 기사를 확정하시겠습니까?")) return;
      try {
        await API.post("/workflow/confirm-articles");
        showToast("기사 선정이 확정되었습니다.", "success");
        loadWorkflow();
        loadArticles();
      } catch (err) { showToast(err.message, "error"); }
    });
  } catch (err) {
    el.innerHTML = `<h2 class="page-title">기사 검토</h2><p class="text-muted">${escHtml(err.message)}</p>`;
  }
}
