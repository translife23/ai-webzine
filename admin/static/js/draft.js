/* 초안 검토 탭 */
async function loadDraft() {
  const el = document.getElementById("tab-draft");
  el.innerHTML = `<h2 class="page-title">초안 검토</h2><p class="text-muted">불러오는 중...</p>`;
  try {
    const draft = await API.get("/workflow/draft");

    if (!draft.tech_report && !draft.newsletter_html) {
      el.innerHTML = `<h2 class="page-title">초안 검토</h2>
        <div class="card"><p class="text-muted">아직 초안이 생성되지 않았습니다.<br>기획 주제를 입력하면 월요일 03:00에 자동으로 생성됩니다.</p></div>`;
      return;
    }

    el.innerHTML = `
      <div class="flex-between"><h2 class="page-title">초안 검토</h2>
        <button class="btn btn-success" id="approve-btn">✓ 승인 및 발행</button>
      </div>

      <div class="card">
        <div class="card-title">기술 분야 기획 보고서</div>
        <div class="markdown-preview" id="tech-preview"></div>
      </div>

      <div class="card">
        <div class="card-title">비기술 분야 기획 보고서</div>
        <div class="markdown-preview" id="nontech-preview"></div>
      </div>

      <div class="card">
        <div class="card-title">뉴스레터 미리보기</div>
        <iframe class="preview-frame" id="newsletter-preview" title="뉴스레터 미리보기"></iframe>
      </div>`;

    // Markdown 렌더링 (간단한 규칙)
    const renderMd = (md) => md
      .replace(/^### (.+)$/gm, "<h3>$1</h3>")
      .replace(/^## (.+)$/gm, "<h2>$1</h2>")
      .replace(/^# (.+)$/gm, "<h1>$1</h1>")
      .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
      .replace(/^- (.+)$/gm, "<li>$1</li>")
      .replace(/\n\n/g, "<br><br>");

    document.getElementById("tech-preview").innerHTML = renderMd(draft.tech_report || "");
    document.getElementById("nontech-preview").innerHTML = renderMd(draft.nontech_report || "");
    const frame = document.getElementById("newsletter-preview");
    frame.srcdoc = draft.newsletter_html || "<p>뉴스레터 없음</p>";

    document.getElementById("approve-btn").addEventListener("click", async () => {
      if (!confirm("초안을 승인하고 웹진 발행 및 뉴스레터 발송을 진행하시겠습니까?\n이 작업은 되돌릴 수 없습니다.")) return;
      try {
        const result = await API.post("/workflow/approve");
        showToast("승인 완료! 발행 파이프라인이 시작됩니다.", "success");
        document.getElementById("approve-btn").disabled = true;
        document.getElementById("approve-btn").textContent = "발행 중...";
        setTimeout(() => { loadWorkflow(); switchTab("workflow"); }, 2000);
      } catch (err) { showToast(err.message, "error"); }
    });
  } catch (err) {
    el.innerHTML = `<h2 class="page-title">초안 검토</h2><p class="text-muted">${escHtml(err.message)}</p>`;
  }
}
