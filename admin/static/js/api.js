/* API 공통 헬퍼 */
const API = {
  async request(method, path, body) {
    const opts = { method, credentials: "include", headers: {} };
    if (body) { opts.headers["Content-Type"] = "application/json"; opts.body = JSON.stringify(body); }
    const res = await fetch("/api" + path, opts);
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);
    return data;
  },
  get:    (path)        => API.request("GET",    path),
  post:   (path, body)  => API.request("POST",   path, body),
  put:    (path, body)  => API.request("PUT",    path, body),
  delete: (path)        => API.request("DELETE", path),
};

function showToast(msg, type = "") {
  const t = document.getElementById("toast");
  t.textContent = msg;
  t.className = "toast" + (type ? " " + type : "");
  t.classList.remove("hidden");
  setTimeout(() => t.classList.add("hidden"), 3000);
}

function escHtml(s) {
  return String(s || "").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
}
