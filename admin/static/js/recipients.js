/* 수신자 관리 탭 */
async function loadRecipients() {
  const el = document.getElementById("tab-recipients");
  el.innerHTML = `<h2 class="page-title">수신자 관리</h2><p class="text-muted">불러오는 중...</p>`;
  try {
    const [data, membersData] = await Promise.all([
      API.get("/recipients/"),
      API.get("/members/").catch(() => ({ members: [] })),
    ]);
    const list = data.recipients || [];
    const members = membersData.members || [];
    const recipientEmails = new Set(list.map(r => r.email));
    const availableMembers = members.filter(m => m.email && !recipientEmails.has(m.email));

    const memberOptions = availableMembers.length
      ? `<option value="">-- 멤버에서 선택 --</option>` +
        availableMembers.map(m =>
          `<option value="${escHtml(m.id)}" data-name="${escHtml(m.username)}" data-email="${escHtml(m.email||"")}">${escHtml(m.username)}${m.email ? " ("+escHtml(m.email)+")" : ""}</option>`
        ).join("")
      : `<option value="">등록 가능한 멤버 없음</option>`;

    el.innerHTML = `
      <div class="flex-between"><h2 class="page-title">수신자 관리</h2>
        <button class="btn btn-primary btn-sm" id="add-recipient-btn">+ 수신자 추가</button>
      </div>
      <div class="card" id="add-form-card" style="display:none">
        <div class="card-title">수신자 추가</div>
        <div class="form-group">
          <label>멤버에서 선택</label>
          <select id="r-member-select">${memberOptions}</select>
        </div>
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
          <tbody>
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
    document.getElementById("r-member-select").addEventListener("change", (e) => {
      const opt = e.target.selectedOptions[0];
      if (opt && opt.value) {
        document.getElementById("r-name").value  = opt.dataset.name || "";
        document.getElementById("r-email").value = opt.dataset.email || "";
      }
    });
    document.getElementById("save-recipient-btn").addEventListener("click", async () => {
      const name  = document.getElementById("r-name").value.trim();
      const email = document.getElementById("r-email").value.trim();
      if (!name || !email) { showToast("이름과 이메일을 입력하세요.", "error"); return; }
      try {
        await API.post("/recipients/", {
          name,
          email,
          department: document.getElementById("r-dept").value.trim(),
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
