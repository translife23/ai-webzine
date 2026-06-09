/* 멤버 관리 탭 */
async function loadMembers() {
  const el = document.getElementById("tab-members");
  el.innerHTML = `<h2 class="page-title">멤버 관리</h2><p class="text-muted">불러오는 중...</p>`;
  try {
    const data = await API.get("/members/");
    const list = data.members || [];

    el.innerHTML = `
      <div class="flex-between"><h2 class="page-title">멤버 관리</h2>
        <button class="btn btn-primary btn-sm" id="add-member-btn">+ 멤버 추가</button>
      </div>
      <div class="card" id="add-member-form" style="display:none">
        <div class="card-title">멤버 추가</div>
        <div class="form-row">
          <div class="form-group"><label>아이디</label><input type="text" id="m-username"></div>
          <div class="form-group"><label>이메일</label><input type="email" id="m-email"></div>
        </div>
        <div class="form-row">
          <div class="form-group"><label>역할</label>
            <select id="m-role"><option value="editor">editor (초안 수정만)</option><option value="admin">admin (발행 권한)</option></select>
          </div>
          <div class="form-group"><label>초기 비밀번호</label><input type="text" id="m-pw" value="admin1234!"></div>
        </div>
        <div class="flex gap-8 mt-16">
          <button class="btn btn-primary btn-sm" id="save-member-btn">저장</button>
          <button class="btn btn-outline btn-sm" id="cancel-member-btn">취소</button>
        </div>
      </div>
      <div class="card">
        <div class="card-title">멤버 목록</div>
        <table class="data-table">
          <thead><tr><th>아이디</th><th>이메일</th><th>역할</th><th>생성일</th><th>작업</th></tr></thead>
          <tbody>
            ${list.map(m => `
              <tr>
                <td><strong>${escHtml(m.username)}</strong></td>
                <td>${escHtml(m.email||"")}</td>
                <td><span class="badge ${m.role==="admin"?"badge-blue":"badge-gray"}">${escHtml(m.role)}</span></td>
                <td class="text-sm text-muted">${m.created_at ? new Date(m.created_at).toLocaleDateString("ko-KR") : ""}</td>
                <td>${m.username !== "admin4web" ? `<button class="btn btn-danger btn-sm" onclick="deleteMember('${m.id}','${escHtml(m.username)}')">삭제</button>` : '<span class="text-muted text-sm">기본 관리자</span>'}</td>
              </tr>`).join("")}
          </tbody>
        </table>
      </div>`;

    document.getElementById("add-member-btn").addEventListener("click", () => {
      document.getElementById("add-member-form").style.display = "";
    });
    document.getElementById("cancel-member-btn").addEventListener("click", () => {
      document.getElementById("add-member-form").style.display = "none";
    });
    document.getElementById("save-member-btn").addEventListener("click", async () => {
      try {
        await API.post("/members/", {
          username: document.getElementById("m-username").value,
          email: document.getElementById("m-email").value,
          role: document.getElementById("m-role").value,
          initial_password: document.getElementById("m-pw").value,
        });
        showToast("멤버가 추가되었습니다.", "success");
        loadMembers();
      } catch (err) { showToast(err.message, "error"); }
    });
  } catch (err) {
    el.innerHTML = `<h2 class="page-title">멤버 관리</h2><p class="text-muted">${escHtml(err.message)}</p>`;
  }
}

async function deleteMember(id, username) {
  if (!confirm(`${username} 멤버를 삭제하시겠습니까?`)) return;
  try {
    await API.delete(`/members/${id}`);
    showToast("삭제 완료", "success");
    loadMembers();
  } catch (err) { showToast(err.message, "error"); }
}
