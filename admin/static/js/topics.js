/* 기획 주제 탭 */
const THEME_AREAS = [
  "공공 AI 서비스 & 규제","AI 기술 & 인프라","AI 산업 & 시장",
  "AI 경제 & 금융","AI 정책 & 거버넌스","AI 사회 & 문화","AI 안보 & 지정학"
];

async function loadTopics() {
  const el = document.getElementById("tab-topics");
  el.innerHTML = `<h2 class="page-title">기획 주제 입력</h2><p class="text-muted">불러오는 중...</p>`;

  let existing = {};
  try { existing = await API.get("/topics/plan"); } catch {}

  const areaOptions = THEME_AREAS.map(a => `<option value="${escHtml(a)}">${escHtml(a)}</option>`).join("");

  const fillValues = (prefix, report) => {
    if (!report) return;
    const f = (id, val) => { const el = document.getElementById(id); if (el) el.value = val || ""; };
    f(`${prefix}-area`,  report.theme_area);
    f(`${prefix}-title`, report.title);
    f(`${prefix}-agenda`,report.agenda);
    f(`${prefix}-persp`, report.perspective);
  };

  el.innerHTML = `
    <h2 class="page-title">기획 주제 입력</h2>
    <form id="topics-form">
      <div class="card">
        <div class="card-title">기술 분야 보고서</div>
        <div class="form-group"><label>테마 영역</label>
          <select id="tech-area">${areaOptions}</select></div>
        <div class="form-group"><label>보고서 제목</label>
          <input type="text" id="tech-title" placeholder="예: 엣지 AI 반도체 경쟁과 국내 파운드리 전략"></div>
        <div class="form-group"><label>핵심 아젠다</label>
          <textarea id="tech-agenda" rows="3" placeholder="이 보고서에서 다루고 싶은 핵심 이슈를 입력하세요"></textarea></div>
        <div class="form-group"><label>분석 관점</label>
          <textarea id="tech-persp" rows="2" placeholder="예: 한국 IT 감리 관점에서 공급망 리스크 중심으로"></textarea></div>
      </div>
      <div class="card">
        <div class="card-title">비기술 분야 보고서</div>
        <div class="form-group"><label>테마 영역</label>
          <select id="non-area">${areaOptions}</select></div>
        <div class="form-group"><label>보고서 제목</label>
          <input type="text" id="non-title" placeholder="예: AI 도입이 금융기관 리스크 관리 체계에 미치는 영향"></div>
        <div class="form-group"><label>핵심 아젠다</label>
          <textarea id="non-agenda" rows="3"></textarea></div>
        <div class="form-group"><label>분석 관점</label>
          <textarea id="non-persp" rows="2"></textarea></div>
      </div>
      <button type="submit" class="btn btn-primary">기획 주제 등록</button>
      <p class="text-muted text-sm mt-16">등록 후 월요일 03:00에 Deep Research가 자동 실행됩니다.</p>
    </form>`;

  // 기존 값 채우기
  if (existing.tech_report) {
    fillValues("tech", existing.tech_report);
    fillValues("non",  existing.nontech_report);
  }

  document.getElementById("topics-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const body = {
      tech_report: {
        theme_area:  document.getElementById("tech-area").value,
        title:       document.getElementById("tech-title").value,
        agenda:      document.getElementById("tech-agenda").value,
        perspective: document.getElementById("tech-persp").value,
      },
      nontech_report: {
        theme_area:  document.getElementById("non-area").value,
        title:       document.getElementById("non-title").value,
        agenda:      document.getElementById("non-agenda").value,
        perspective: document.getElementById("non-persp").value,
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
