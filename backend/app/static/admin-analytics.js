(() => {
  "use strict";

  const section = document.querySelector('[data-section="analytics"]');
  if (!section) return;

  const labels = section.querySelectorAll(".an-stats .an-l");
  const labelText = [
    "confirmed pageviews",
    "confirmed visitor-days",
    "confirmation rate",
    "today confirmed",
  ];
  labels.forEach((element, index) => {
    if (labelText[index]) element.textContent = labelText[index];
  });
  const description = section.querySelector(".field-desc");
  if (description) {
    description.textContent = "// Turnstile-confirmed humans only; read-only.";
  }
  const chartLabel = section.querySelector(".an-chart-wrap")?.previousElementSibling;
  if (chartLabel) chartLabel.textContent = "Confirmed pageviews over time";
  const recentLabel = document.querySelector("#an-recent")?.previousElementSibling;
  if (recentLabel) recentLabel.textContent = "Recent confirmed visits";

  const style = document.createElement("style");
  style.textContent = `
    .an-verified{display:inline-flex;align-items:center;gap:5px;margin-left:auto;
      color:var(--acc);border:1px solid var(--acc-dim);border-radius:999px;
      padding:2px 7px;font-size:9px;text-transform:uppercase;letter-spacing:.45px}
    .an-diagnostics{margin-top:18px;border:1px solid var(--line);border-radius:6px;
      background:var(--bg);padding:0 12px}
    .an-diagnostics summary{cursor:pointer;padding:11px 0;color:var(--ink-mute);
      font:11px var(--mono);text-transform:uppercase;letter-spacing:.55px}
    .an-diagnostic-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));
      gap:6px;padding:0 0 12px}
    .an-diagnostic-grid .an-row{min-width:0}
    @media(max-width:720px){.an-diagnostic-grid{grid-template-columns:1fr}}
  `;
  document.head.appendChild(style);

  const details = document.createElement("details");
  details.className = "an-diagnostics";
  details.innerHTML = `
    <summary>Aggregated filter diagnostics</summary>
    <div class="an-diagnostic-grid" id="an-diagnostics"></div>
  `;
  section.appendChild(details);

  const escapeHtml = (value) => String(value ?? "").replace(
    /[&<>"]/g,
    (character) => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"}[character]),
  );

  async function loadConfirmedAnalytics() {
    const days = Number(document.querySelector("#an-days")?.value || 30);
    const response = await fetch(`/api/analytics?days=${days}`, {
      credentials: "same-origin",
      headers: {"Accept": "application/json"},
    });
    if (!response.ok) return;
    const data = await response.json();
    const diagnostics = data.diagnostics || {};
    const perDay = data.per_day || [];
    const today = new Date().toISOString().slice(0, 10);
    const todayRow = perDay.find((row) => row.date === today);

    document.querySelector("#an-total").textContent = data.confirmed_pageviews ?? 0;
    document.querySelector("#an-unique").textContent = data.confirmed_visitor_days ?? 0;
    document.querySelector("#an-avg").textContent = `${diagnostics.confirmation_rate ?? 0}%`;
    document.querySelector("#an-today").textContent = todayRow?.visits ?? 0;

    const recent = data.recent || [];
    document.querySelector("#an-recent").innerHTML = recent.map((row) => `
      <div class="an-row">
        <span class="k">${escapeHtml(row.path)}</span>
        <span class="t">${escapeHtml((row.at || "").slice(5, 16))}</span>
        <span class="an-verified">Turnstile verified</span>
      </div>
    `).join("") || `
      <div class="an-row"><span class="k" style="color:var(--ink-mute)">
        no confirmed visits yet
      </span></div>
    `;

    const diagnosticRows = [
      ["Requests in analytics scope", diagnostics.total_requests],
      ["Discarded before confirmation", diagnostics.discarded_requests],
      ["Known verified bots", diagnostics.known_bot],
      ["Missing browser confirmation", diagnostics.missing_browser_confirmation],
      ["Turnstile failed", diagnostics.turnstile_failed],
      ["Rate limited", diagnostics.rate_limited],
      ["Invalid or replayed seed", diagnostics.invalid_seed],
      ["Missing Fetch Metadata", diagnostics.missing_fetch_metadata],
      ["Successful confirmations", diagnostics.confirmed],
    ];
    document.querySelector("#an-diagnostics").innerHTML = diagnosticRows.map(
      ([name, value]) => `
        <div class="an-row">
          <span class="k">${escapeHtml(name)}</span>
          <span class="v">${Number(value || 0)}</span>
        </div>
      `,
    ).join("");
  }

  document.querySelector("#an-days")?.addEventListener("change", () => {
    window.setTimeout(loadConfirmedAnalytics, 0);
  });
  document.querySelectorAll('[data-tab="analytics"]').forEach((button) => {
    button.addEventListener("click", () => {
      window.setTimeout(loadConfirmedAnalytics, 0);
    });
  });
})();
