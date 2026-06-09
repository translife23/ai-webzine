/* 내 계정 탭 */
async function loadAccount() {
  const el = document.getElementById("tab-account");
  try {
    const me = await API.get("/auth/me");
    el.innerHTML = `
      <h2 class="page-title">내 계정</h2>
      <div class="card" style="max-width:480px">
        <div class="card-title">계정 정보</div>
        <table class="data-table" style="margin-bottom:24px">
          <tr><td class="text-muted">아이디</td><td><strong>${escHtml(me.username)}</strong></td></tr>
          <tr><td class="text-muted">역할</td><td><span class="badge ${me.role==="admin"?"badge-blue":"badge-gray"}">${escHtml(me.role)}</span></td></tr>
        </table>
        <div class="card-title">비밀번호 변경</div>
        <div class="form-group"><label>현재 비밀번호</label><input type="password" id="pw-current"></div>
        <div class="form-group"><label>새 비밀번호 (8자 이상)</label><input type="password" id="pw-new"></div>
        <div class="form-group"><label>새 비밀번호 확인</label><input type="password" id="pw-confirm"></div>
        <button class="btn btn-primary mt-16" id="change-pw-btn">비밀번호 변경</button>
        <p id="pw-error" class="error-msg hidden"></p>
      </div>`;

    document.getElementById("change-pw-btn").addEventListener("click", async () => {
      const errEl = document.getElementById("pw-error");
      errEl.classList.add("hidden");
      const cur = document.getElementById("pw-current").value;
      const nw = document.getElementById("pw-new").value;
      const cf = document.getElementById("pw-confirm").value;
      if (nw !== cf) { errEl.textContent = "새 비밀번호가 일치하지 않습니다."; errEl.classList.remove("hidden"); return; }
      if (nw.length < 8) { errEl.textContent = "8자 이상 입력해 주세요."; errEl.classList.remove("hidden"); return; }
      try {
        await API.put("/auth/password", { current_password: cur, new_password: nw });
        showToast("비밀번호가 변경되었습니다.", "success");
        document.getElementById("pw-current").value = "";
        document.getElementById("pw-new").value = "";
        document.getElementById("pw-confirm").value = "";
      } catch (err) { errEl.textContent = err.message; errEl.classList.remove("hidden"); }
    });
  } catch (err) {
    el.innerHTML = `<h2 class="page-title">내 계정</h2><p class="text-muted">${escHtml(err.message)}</p>`;
  }
}
