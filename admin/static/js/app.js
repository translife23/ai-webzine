/* 앱 진입점 — 로그인, 탭 라우팅 */

const STATUS_LABELS = {
  IDLE: { text: "대기", badge: "badge-gray" },
  NEWS_SEARCHING: { text: "뉴스 검색 중", badge: "badge-orange" },
  AWAITING_ADMIN_REVIEW: { text: "기사 검토 대기", badge: "badge-blue" },
  ARTICLES_CONFIRMED: { text: "기사 확정 완료", badge: "badge-green" },
  THEME_PLAN_READY: { text: "기획 주제 입력 완료", badge: "badge-green" },
  GENERATING: { text: "보고서 생성 중", badge: "badge-orange" },
  DRAFT_READY: { text: "초안 검토 대기", badge: "badge-blue" },
  PUBLISHING: { text: "발행 중", badge: "badge-orange" },
  PUBLISHED: { text: "발행 완료", badge: "badge-green" },
  PUBLISH_FAILED: { text: "발행 실패", badge: "badge-red" },
};
window.STATUS_LABELS = STATUS_LABELS;

document.addEventListener("DOMContentLoaded", async () => {
  // 로그인 상태 확인
  try {
    const me = await API.get("/auth/me");
    showMainApp(me);
  } catch {
    showLoginScreen();
  }
});

function showLoginScreen() {
  document.getElementById("login-screen").classList.remove("hidden");
  document.getElementById("main-app").classList.add("hidden");
  document.getElementById("login-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const errEl = document.getElementById("login-error");
    try {
      const me = await API.post("/auth/login", {
        username: document.getElementById("username").value,
        password: document.getElementById("password").value,
      });
      showMainApp(me);
    } catch (err) {
      errEl.textContent = err.message;
      errEl.classList.remove("hidden");
    }
  });
}

function showMainApp(me) {
  document.getElementById("login-screen").classList.add("hidden");
  document.getElementById("main-app").classList.remove("hidden");

  // 탭 라우팅
  document.querySelectorAll(".nav-item").forEach((el) => {
    el.addEventListener("click", (e) => {
      e.preventDefault();
      switchTab(el.dataset.tab);
    });
  });

  // 로그아웃
  document.getElementById("logout-btn").addEventListener("click", async () => {
    await API.post("/auth/logout");
    location.reload();
  });

  // 기본 탭 로드
  switchTab("workflow");
}

function switchTab(name) {
  document.querySelectorAll(".tab-panel").forEach((p) => { p.classList.add("hidden"); p.classList.remove("active"); });
  document.querySelectorAll(".nav-item").forEach((n) => n.classList.remove("active"));
  const panel = document.getElementById("tab-" + name);
  panel.classList.remove("hidden");
  panel.classList.add("active");
  document.querySelector(`[data-tab="${name}"]`).classList.add("active");

  const loaders = {
    workflow:   loadWorkflow,
    articles:   loadArticles,
    topics:     loadTopics,
    draft:      loadDraft,
    recipients: loadRecipients,
    members:    loadMembers,
    account:    loadAccount,
  };
  if (loaders[name]) loaders[name]();
}
