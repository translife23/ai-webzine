/* AI 웹진 — 인터랙션 스크립트 */

// details 요약 텍스트 토글
document.querySelectorAll("details").forEach((el) => {
  const summary = el.querySelector("summary");
  if (!summary) return;
  el.addEventListener("toggle", () => {
    summary.textContent = el.open ? "접기" : "전문 보기";
  });
});
