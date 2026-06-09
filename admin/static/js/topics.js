/* 기획 주제 탭 */
async function loadTopics() {
  const el = document.getElementById("tab-topics");
  el.innerHTML = `<h2 class="page-title">기획 주제 입력</h2><p class="text-muted">불러오는 중...</p>`;

  let existing = {};
  try { existing = await API.get("/topics/plan"); } catch {}

  const fillValues = (prefix, report) => {
    if (!report) return;
    const f = (id, val) => { const el = document.getElementById(id); if (el) el.value = val || ""; };
    f(`${prefix}-title`, report.title);
    f(`${prefix}-agenda`, report.agenda);
    f(`${prefix}-persp`,  report.perspective);
  };

  el.innerHTML = `
    <h2 class="page-title">기획 주제 입력</h2>
    <p class="text-muted" style="margin-bottom:20px">테마 영역은 Routine B가 자동 선택합니다.</p>
    <form id="topics-form">
      <div class="card">
        <div class="card-title">보고서 1</div>
        <div class="form-group"><label>보고서 제목</label>
          <input type="text" id="r1-title" placeholder="예: 엣지 AI 반도체 경쟁과 국내 파운드리 전략"></div>
        <div class="form-group"><label>핵심 아젠다</label>
          <textarea id="r1-agenda" rows="3" placeholder="이 보고서에서 다루고 싶은 핵심 이슈를 입력하세요"></textarea></div>
        <div class="form-group"><label>분석 관점</label>
          <textarea id="r1-persp" rows="2" placeholder="예: 한국 IT 감리 관점에서 공급망 리스크 중심으로"></textarea></div>
      </div>
      <div class="card">
        <div class="card-title">보고서 2</div>
        <div class="form-group"><label>보고서 제목</label>
          <input type="text" id="r2-title" placeholder="예: AI 도입이 금융기관 리스크 관리 체계에 미치는 영향"></div>
        <div class="form-group"><label>핵심 아젠다</label>
          <textarea id="r2-agenda" rows="3"></textarea></div>
        <div class="form-group"><label>분석 관점</label>
          <textarea id="r2-persp" rows="2"></textarea></div>
      </div>
      <button type="submit" class="btn btn-primary">기획 주제 등록</button>
      <p class="text-muted text-sm mt-16">등록 후 월요일 03:00에 Deep Research가 자동 실행됩니다.</p>
    </form>`;

  if (existing.report_1) {
    fillValues("r1", existing.report_1);
    fillValues("r2", existing.report_2);
  }

  document.getElementById("topics-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const body = {
      report_1: {
        title:       document.getElementById("r1-title").value,
        agenda:      document.getElementById("r1-agenda").value,
        perspective: document.getElementById("r1-persp").value,
      },
      report_2: {
        title:       document.getElementById("r2-title").value,
        agenda:      document.getElementById("r2-agenda").value,
        perspective: document.getElementById("r2-persp").value,
      },
    };
    try {
      const method = existing.submitted_at ? "put" : "post";
      await API[method]("/topics/plan", body);
      showToast("기획 주제가 등록되었습니다.", "success");
      existing.submitted_at = new Date().toISOString();
    } catch (err) { showToast(err.message, "error"); }
  });
}
