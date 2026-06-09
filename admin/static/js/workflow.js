/* 워크플로 현황 탭 */
async function loadWorkflow() {
  const el = document.getElementById("tab-workflow");
  el.innerHTML = `<h2 class="page-title">워크플로 현황</h2><p class="text-muted">불러오는 중...</p>`;
  try {
    const status = await API.get("/workflow/status");
    const s = STATUS_LABELS[status.status] || { text: status.status, badge: "badge-gray" };
    const tl = status.timeline || {};
    const steps = [
      { key: "NEWS_SEARCHING",        label: "뉴스 검색",   time: tl.news_search_completed },
      { key: "ARTICLES_CONFIRMED",    label: "기사 확정",   time: tl.articles_confirmed },
      { key: "THEME_PLAN_READY",      label: "기획 주제",   time: tl.theme_plan_submitted },
      { key: "DRAFT_READY",           label: "초안 생성",   time: tl.draft_ready },
      { key: "PUBLISHED",             label: "발행 완료",   time: tl.published },
    ];
    const ORDER = Object.keys(STATUS_LABELS);
    const currentIdx = ORDER.indexOf(status.status);

    const stepsHtml = steps.map((step, i) => {
      const stepIdx = ORDER.indexOf(step.key);
      let cls = "pending";
      if (stepIdx < currentIdx) cls = "done";
      else if (stepIdx === currentIdx) cls = "active";
      return `<span class="step ${cls}">${step.label}${step.time ? `<small class="text-muted"> ✓</small>` : ""}</span>${i < steps.length-1 ? '<span class="step-arrow">›</span>' : ""}`;
    }).join("");

    let actionHtml = "";
    if (status.status === "AWAITING_ADMIN_REVIEW") {
      actionHtml = `<a class="btn btn-primary btn-sm mt-16" href="#" onclick="switchTab('articles');return false">기사 검토하기 →</a>`;
    } else if (status.status === "ARTICLES_CONFIRMED") {
      actionHtml = `<a class="btn btn-primary btn-sm mt-16" href="#" onclick="switchTab('topics');return false">기획 주제 입력하기 →</a>`;
    } else if (status.status === "DRAFT_READY") {
      actionHtml = `<a class="btn btn-success btn-sm mt-16" href="#" onclick="switchTab('draft');return false">초안 검토 및 승인하기 →</a>`;
    }

    el.innerHTML = `
      <h2 class="page-title">워크플로 현황</h2>
      <div class="card">
        <div class="flex-between">
          <div>
            <span class="text-muted text-sm">현재 주차</span>
            <div style="font-size:20px;font-weight:700;margin-top:4px">${escHtml(status.week || "")}</div>
          </div>
          <span class="badge ${s.badge}" style="font-size:14px;padding:6px 16px">${s.text}</span>
        </div>
        <div class="steps mt-16">${stepsHtml}</div>
        ${actionHtml}
      </div>
      <div class="card">
        <div class="card-title">단계별 완료 시각</div>
        <table class="data-table">
          ${steps.filter(s => s.time).map(s => `
            <tr><td class="text-muted">${s.label}</td><td>${new Date(s.time).toLocaleString("ko-KR")}</td></tr>
          `).join("")}
          ${steps.every(s => !s.time) ? '<tr><td colspan="2" class="text-muted">아직 진행된 단계가 없습니다.</td></tr>' : ""}
        </table>
      </div>`;
  } catch (err) {
    el.innerHTML = `<h2 class="page-title">워크플로 현황</h2><p class="text-muted">불러오기 실패: ${escHtml(err.message)}</p>`;
  }
}
