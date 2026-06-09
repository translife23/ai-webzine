/* 수신자 관리 탭 */
async function loadRecipients() {
  const el = document.getElementById("tab-recipients");
  el.innerHTML = `<h2 class="page-title">수신자 관리</h2><p class="text-muted">불러오는 중...</p>`;
  try {
    const data = await API.get("/recipients/");
    const list = data.recipients || [];

    el.innerHTML = `
      <div class="flex-between"><h2 class="page-title">수신자 관리</h2>
        <button class="btn btn-primary btn-sm" id="add-recipient-btn">+ 수신자 추가</button>
      </div>
      <div class="card" id="add-form-card" style="display:none">
        <div class="card-title">수신자 추가</div>
        <div class="form-row">
          <div class="form-group"><label>이름</label><input type="text" id="r-name"></div>
          <div class="form-group"><label>이메일</label><input type="email" id="r-email"></div>
        </div>
        <div class="form-group"><label>소속</label><input type="text" id="r-dept"></div>
        <div class="flex gap-8 mt-16">
          <button class="btn btn-primary btn-sm" id="save-recipient-btn">저장</button>
          <button class="btn btn-outline btn-sm" id="cancel-recipient-btn">취소</button>
        </div>
      </div>
      <div class="card">
        <div class="card-title">수신자 목록 (총 ${list.length}명, 활성 ${list.filter(r=>r.active).length}명)</div>
        <table class="data-table">
          <thead><tr><th>이름</th><th>이메일</th><th>소속</th><th>상태</th><th>작업</th></tr></thead>
          <tbody id="recipients-tbody">
            ${list.map(r => `
              <tr>
                <td>${escHtml(r.name)}</td>
                <td>${escHtml(r.email)}</td>
                <td>${escHtml(r.department||"")}</td>
                <td><span class="badge ${r.active?"badge-green":"badge-gray"}">${r.active?"활성":"비활성"}</span></td>
                <td>
                  <button class="btn btn-outline btn-sm" onclick="toggleRecipient('${r.id}',${!r.active})">${r.active?"비활성화":"활성화"}</button>
                  <button class="btn btn-danger btn-sm" onclick="deleteRecipient('${r.id}','${escHtml(r.name)}')">삭제</button>
                </td>
              </tr>`).join("")}
          </tbody>
        </table>
      </div>`;

    document.getElementById("add-recipient-btn").addEventListener("click", () => {
      document.getElementById("add-form-card").style.display = "";
    });
    document.getElementById("cancel-recipient-btn").addEventListener("click", () => {
      document.getElementById("add-form-card").style.display = "none";
    });
    document.getElementById("save-recipient-btn").addEventListener("click", async () => {
      try {
        await API.post("/recipients/", {
          name: document.getElementById("r-name").value,
          email: document.getElementById("r-email").value,
          department: document.getElementById("r-dept").value,
        });
        showToast("수신자가 추가되었습니다.", "success");
        loadRecipients();
      } catch (err) { showToast(err.message, "error"); }
    });
  } catch (err) {
    el.innerHTML = `<h2 class="page-title">수신자 관리</h2><p class="text-muted">${escHtml(err.message)}</p>`;
  }
}

async function toggleRecipient(id, active) {
  try {
    await API.put(`/recipients/${id}`, { active });
    showToast(active ? "활성화 완료" : "비활성화 완료", "success");
    loadRecipients();
  } catch (err) { showToast(err.message, "error"); }
}

async function deleteRecipient(id, name) {
  if (!confirm(`${name} 수신자를 삭제하시겠습니까?`)) return;
  try {
    await API.delete(`/recipients/${id}`);
    showToast("삭제 완료", "success");
    loadRecipients();
  } catch (err) { showToast(err.message, "error"); }
}
