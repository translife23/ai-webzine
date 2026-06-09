/* 기획보고서 검토 탭 */
async function loadDraft() {
  const el = document.getElementById("tab-draft");
  el.innerHTML = `<h2 class="page-title">기획보고서 검토</h2><p class="text-muted">불러오는 중...</p>`;
  try {
    const draft = await API.get("/workflow/draft");

    if (!draft.report) {
      el.innerHTML = `<h2 class="page-title">기획보고서 검토</h2>
        <div class="card"><p class="text-muted">아직 보고서가 생성되지 않았습니다.<br>기획 주제를 입력하면 월요일 03:00에 자동으로 생성됩니다.</p></div>`;
      return;
    }

    el.innerHTML = `
      <div class="flex-between" style="margin-bottom:24px">
        <h2 class="page-title" style="margin:0">기획보고서 검토</h2>
        <button class="btn btn-success" id="approve-btn">✓ 승인 및 발행</button>
      </div>
      <div class="card" style="padding:0;overflow:hidden">
        <div style="background:#1A56DB;padding:20px 24px;color:#fff">
          <div id="report-title-display" style="font-size:18px;font-weight:700"></div>
          <div style="font-size:13px;color:#93C5FD;margin-top:4px">${escHtml(draft.week)} 기획 보고서</div>
        </div>
        <div id="report-preview" style="padding:24px;font-size:14px;line-height:1.8;color:#1E293B;max-height:70vh;overflow-y:auto"></div>
      </div>
      ${draft.newsletter_html ? `
      <div class="card" style="margin-top:20px">
        <div class="card-title">뉴스레터 미리보기</div>
        <iframe class="preview-frame" id="newsletter-preview" title="뉴스레터 미리보기"></iframe>
      </div>` : ""}`;

    // 마크다운 → HTML 렌더링 (웹진 스타일)
    const rendered = renderReportMd(draft.report);
    document.getElementById("report-title-display").textContent = extractMdTitle(draft.report);
    document.getElementById("report-preview").innerHTML = rendered;

    if (draft.newsletter_html) {
      document.getElementById("newsletter-preview").srcdoc = draft.newsletter_html;
    }

    document.getElementById("approve-btn").addEventListener("click", async () => {
      if (!confirm("초안을 승인하고 웹진 발행 및 뉴스레터 발송을 진행하시겠습니까?\n이 작업은 되돌릴 수 없습니다.")) return;
      try {
        await API.post("/workflow/approve");
        showToast("승인 완료! 발행 파이프라인이 시작됩니다.", "success");
        document.getElementById("approve-btn").disabled = true;
        document.getElementById("approve-btn").textContent = "발행 중...";
        setTimeout(() => { loadWorkflow(); switchTab("workflow"); }, 2000);
      } catch (err) { showToast(err.message, "error"); }
    });
  } catch (err) {
    el.innerHTML = `<h2 class="page-title">기획보고서 검토</h2><p class="text-muted">${escHtml(err.message)}</p>`;
  }
}

function extractMdTitle(md) {
  const m = md.match(/^# (.+)$/m);
  return m ? m[1] : "기획 보고서";
}

function renderReportMd(md) {
  const lines = md.split("\n");
  const out = [];
  let inUl = false;

  for (const line of lines) {
    if (line.startsWith("# ")) {
      if (inUl) { out.push("</ul>"); inUl = false; }
      // h1은 헤더에 표시하므로 건너뜀
    } else if (line.startsWith("## ")) {
      if (inUl) { out.push("</ul>"); inUl = false; }
      out.push(`<h2 style="font-size:16px;font-weight:700;margin:20px 0 8px;color:#1239A6;border-left:4px solid #1A56DB;padding-left:10px">${escHtml(line.slice(3))}</h2>`);
    } else if (line.startsWith("### ")) {
      if (inUl) { out.push("</ul>"); inUl = false; }
      out.push(`<h3 style="font-size:14px;font-weight:700;margin:14px 0 6px;color:#1E293B">${escHtml(line.slice(4))}</h3>`);
    } else if (/^[-*] /.test(line)) {
      if (!inUl) { out.push('<ul style="margin:6px 0 10px 20px;padding:0">'); inUl = true; }
      const item = line.slice(2).replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
      out.push(`<li style="margin-bottom:4px">${item}</li>`);
    } else if (line.trim() === "") {
      if (inUl) { out.push("</ul>"); inUl = false; }
      out.push("");
    } else {
      if (inUl) { out.push("</ul>"); inUl = false; }
      const p = line.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>").replace(/\*(.+?)\*/g, "<em>$1</em>");
      out.push(`<p style="margin-bottom:8px">${p}</p>`);
    }
  }
  if (inUl) out.push("</ul>");
  return out.join("\n");
}
