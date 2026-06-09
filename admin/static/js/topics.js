/* 기획 주제 탭 */
async function loadTopics() {
  const el = document.getElementById("tab-topics");
  el.innerHTML = `<h2 class="page-title">기획 주제</h2><p class="text-muted">불러오는 중...</p>`;

  let existing = {};
  let history = [];
  try { existing = await API.get("/topics/plan"); } catch {}
  try { const h = await API.get("/topics/history"); history = h.history || []; } catch {}

  const report = existing.report_1 || null;
  const submitted = !!existing.submitted_at;
  const week = existing.week || "";

  const STATUS_KO = {
    IDLE: "대기", NEWS_SEARCHING: "뉴스 검색 중", ARTICLES_CONFIRMED: "기사 확정",
    THEME_PLAN_READY: "주제 등록됨", GENERATING: "보고서 생성 중",
    DRAFT_READY: "초안 검토 대기", PUBLISHING: "발행 중", PUBLISHED: "발행 완료",
  };

  const currentBlock = report ? `
    <div class="card" style="background:#f8fafc;border:1px solid #e2e8f0;margin-bottom:24px">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
        <div class="card-title" style="margin:0">이번 주(${escHtml(week)}) 등록된 주제</div>
        <button class="btn btn-sm" id="edit-btn" style="font-size:12px;padding:4px 12px">수정</button>
      </div>
      <div style="font-size:14px;color:#374151">
        <div style="margin-bottom:6px"><span style="color:#6b7280;font-size:12px">기획보고서 주제</span><br><strong>${escHtml(report.agenda || "")}</strong></div>
        <div><span style="color:#6b7280;font-size:12px">분석 관점</span><br>${escHtml(report.perspective || "")}</div>
      </div>
    </div>` : `
    <div class="card" style="background:#fff7ed;border:1px solid #fed7aa;margin-bottom:24px">
      <div style="color:#92400e;font-size:14px">이번 주(${escHtml(week)}) 기획 주제: <strong>미정</strong></div>
    </div>`;

  // 히스토리 (현재 주차 제외)
  const pastItems = history.filter(h => h.week !== week);
  const historyBlock = pastItems.length ? `
    <div class="card" style="margin-top:24px">
      <div class="card-title">기획 주제 이력</div>
      <table class="data-table">
        <thead><tr>
          <th>주차</th><th>기획보고서 주제</th><th>분석 관점</th><th>상태</th>
        </tr></thead>
        <tbody>${pastItems.map(h => `
          <tr>
            <td style="white-space:nowrap">${escHtml(h.week)}</td>
            <td>${escHtml(h.agenda)}</td>
            <td style="color:#64748b">${escHtml(h.perspective)}</td>
            <td><span class="badge ${h.status==='PUBLISHED'?'badge-green':'badge-gray'}">${escHtml(STATUS_KO[h.status]||h.status)}</span></td>
          </tr>`).join("")}
        </tbody>
      </table>
    </div>` : "";

  el.innerHTML = `
    <h2 class="page-title">기획 주제</h2>
    ${currentBlock}
    <form id="topics-form">
      <div class="card">
        <div class="form-group">
          <label>기획보고서 주제 <span style="color:#6b7280;font-weight:400;font-size:12px">(보고서 제목은 AI가 자동 생성)</span></label>
          <textarea id="r-agenda" rows="3" placeholder="예: 글로벌 AI 반도체 공급망 재편과 한국의 대응 전략"></textarea>
        </div>
        <div class="form-group">
          <label>분석 관점</label>
          <textarea id="r-persp" rows="2" placeholder="예: 정보시스템 감리 관점에서 AI 인프라 리스크 중심으로"></textarea>
        </div>
        <button type="submit" class="btn btn-primary" id="submit-btn">${submitted ? "수정 저장" : "기획 주제 등록"}</button>
        <p class="text-muted text-sm mt-16">등록 후 월요일 03:00에 Deep Research가 자동 실행됩니다.</p>
      </div>
    </form>
    ${historyBlock}`;

  if (report) {
    document.getElementById("r-agenda").value = report.agenda || "";
    document.getElementById("r-persp").value  = report.perspective || "";
    document.getElementById("topics-form").style.display = "none";

    document.getElementById("edit-btn").addEventListener("click", () => {
      document.getElementById("topics-form").style.display = "block";
      document.getElementById("edit-btn").style.display = "none";
    });
  }

  document.getElementById("topics-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const body = {
      report_1: {
        agenda:      document.getElementById("r-agenda").value.trim(),
        perspective: document.getElementById("r-persp").value.trim(),
      },
    };
    if (!body.report_1.agenda) { showToast("기획보고서 주제를 입력하세요.", "error"); return; }
    try {
      const method = submitted ? "put" : "post";
      await API[method]("/topics/plan", body);
      showToast("기획 주제가 등록되었습니다.", "success");
      loadTopics();
    } catch (err) { showToast(err.message, "error"); }
  });
}
