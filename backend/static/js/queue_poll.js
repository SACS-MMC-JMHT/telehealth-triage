// Poll the /queue/poll/ endpoint every 30 s and update the badge.
(function () {
  const badge = document.getElementById("new-count");
  if (!badge) return;                       // only active on queue page

  async function poll() {
    try {
      const resp = await fetch("/queue/poll/", { credentials: "same-origin" });
      if (!resp.ok) return;
      const { new_count } = await resp.json();
      badge.textContent = new_count > 0 ? `(${new_count} new)` : "";
    } catch (_) { /* silent — offline tolerance */ }
  }

  poll();
  setInterval(poll, 30_000);
})();
