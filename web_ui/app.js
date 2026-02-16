const state = {
  baseUrl: window.location.origin,
  token: localStorage.getItem("swarmz_token") || "",
  runs: [],
  currentRunId: null,
  offlineMode: false,
};

let deferredPrompt = null;

function $(id) { return document.getElementById(id); }
function setText(id, text) { const el = $(id); if (el) el.textContent = text; }

function setPairStatus(text, ok) {
  const pill = $("pairStatus");
  if (!pill) return;
  pill.textContent = text;
  pill.style.background = ok ? "rgba(52,211,153,0.15)" : "rgba(248,113,113,0.15)";
  pill.style.borderColor = ok ? "rgba(52,211,153,0.5)" : "rgba(248,113,113,0.5)";
}

function setDetailStatus(text, ok) {
  const pill = $("detailStatus");
  if (!pill) return;
  pill.textContent = text || "";
  pill.style.background = ok ? "rgba(52,211,153,0.15)" : "rgba(148,163,184,0.10)";
  pill.style.borderColor = ok ? "rgba(52,211,153,0.5)" : "rgba(148,163,184,0.25)";
}

function setPill(id, text, ok) {
  const pill = $(id);
  if (!pill) return;
  pill.textContent = text;
  if (ok === true) {
    pill.style.background = "rgba(52,211,153,0.15)";
    pill.style.borderColor = "rgba(52,211,153,0.5)";
  } else if (ok === false) {
    pill.style.background = "rgba(248,113,113,0.15)";
    pill.style.borderColor = "rgba(248,113,113,0.5)";
  } else {
    pill.style.background = "rgba(124,58,237,0.18)";
    pill.style.borderColor = "rgba(124,58,237,0.4)";
  }
}

function setHint(text) { setText("pairHint", text); }

async function loadRuntimeConfig() {
  try {
    const res = await fetch("/config/runtime.json", { cache: "no-store" });
    if (!res.ok) return;
    const cfg = await res.json();
    if (cfg && cfg.apiBaseUrl) {
      state.baseUrl = normalizeBaseUrl(cfg.apiBaseUrl);
      const baseUrlEl = $("baseUrl");
      if (baseUrlEl) baseUrlEl.value = state.baseUrl;
    }
    if (cfg && typeof cfg.offlineMode === "boolean") {
      state.offlineMode = cfg.offlineMode;
    }
  } catch (e) {
    // best-effort; fall back to window origin
  }
}

function normalizeBaseUrl(u) {
  try { return new URL(u).origin; } catch { return window.location.origin; }
}

async function apiFetch(path, opts = {}) {
  const base = normalizeBaseUrl(state.baseUrl);
  const url = `${base}${path}`;

  const headers = Object.assign({}, opts.headers || {});
  if (state.token) headers["Authorization"] = `Bearer ${state.token}`;
  if (!headers["Content-Type"] && opts.body) headers["Content-Type"] = "application/json";

  let res;
  try {
    res = await fetch(url, {
      method: opts.method || "GET",
      headers,
      body: opts.body || undefined,
    });
  } catch (e) {
    setHint(`Network error: ${String(e)}`);
    throw e;
  }

  let data = null;
  const ct = res.headers.get("content-type") || "";
  if (ct.includes("application/json")) {
    try { data = await res.json(); } catch { data = null; }
  } else {
    try { data = await res.text(); } catch { data = null; }
  }

  if (res.status === 401) {
    setPairStatus("Not paired", false);
    setHint("Unauthorized. Pair again to get a token.");
  }

  if (!res.ok) {
    const msg = typeof data === "string" ? data : JSON.stringify(data);
    const err = new Error(`HTTP ${res.status}: ${msg}`);
    err.status = res.status;
    err.data = data;
    throw err;
  }

  return data;
}

function escapeHtml(s) {
  return String(s)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function renderRuns() {
  const ul = $("runsList");
  if (!ul) return;
  ul.innerHTML = "";

  if (!state.runs || state.runs.length === 0) {
    const li = document.createElement("li");
    li.className = "list-item";
    li.textContent = "No runs yet.";
    ul.appendChild(li);
    return;
  }

  for (const r of state.runs) {
    const li = document.createElement("li");
    li.className = "list-item";
    li.style.cursor = "pointer";

    const id = r.run_id || r.id || r.mission_id || "";
    const status = r.status || r.state || "";
    const title = r.goal || r.intent || r.name || id;

    li.innerHTML = `
      <div class="row">
        <div class="col">
          <div class="list-title">${escapeHtml(title)}</div>
          <div class="list-sub">${escapeHtml(id)}</div>
        </div>
        <div class="pill">${escapeHtml(status)}</div>
      </div>
    `;

    li.addEventListener("click", () => {
      state.currentRunId = id;
      loadRunDetail().catch(() => {});
    });

    ul.appendChild(li);
  }
}

function renderAudit(entries) {
  const box = $("auditList");
  if (!box) return;

  if (!entries || entries.length === 0) {
    box.textContent = "No audit entries.";
    return;
  }

  const lines = entries.map((e) => {
    const ts = e.ts || e.timestamp || "";
    const t = e.type || e.event || "";
    const msg = e.msg || e.message || "";
    return `${ts}  ${t}  ${msg}`.trim();
  });

  box.textContent = lines.slice(-50).join("\n");
}

function renderDetail(obj) {
  const body = $("detailBody");
  if (!body) return;

  if (!obj) {
    body.textContent = "No run selected.";
    setText("detailTitle", "Select a run");
    setDetailStatus("", false);
    return;
  }

  const id = obj.run_id || obj.id || obj.mission_id || state.currentRunId || "";
  const status = obj.status || obj.state || "";
  setText("detailTitle", id || "Run detail");
  setDetailStatus(status, status && String(status).toLowerCase().includes("done"));

  body.textContent = JSON.stringify(obj, null, 2);
}

async function refreshPairingInfo() {
  try {
    const info = await apiFetch("/v1/pairing/info");
    const pinRules = info && (info.pin_hint || info.hint || info.mode || "");
    setHint(pinRules ? String(pinRules) : "Enter the PIN from the host console. Base URL defaults to this page.");
    return info;
  } catch (e) {
    setHint(`Pairing info failed: ${e.message}`);
    return null;
  }
}

async function pairNow() {
  const pin = ($("pinInput")?.value || "").trim();
  if (!pin) { setHint("Enter PIN."); return; }

  try {
    const resp = await apiFetch("/v1/pairing/pair", {
      method: "POST",
      body: JSON.stringify({ pin }),
    });

    const token =
      (resp && (resp.token || resp.access_token || resp.bearer || resp.key)) ||
      (typeof resp === "string" ? resp : "");

    if (!token) {
      setPairStatus("Paired (token missing)", true);
      setHint("Pair succeeded but token not found in response. Check /v1/pairing/pair output.");
      return;
    }

    state.token = token;
    localStorage.setItem("swarmz_token", token);
    setPairStatus("Paired", true);
    setHint("Token stored. You can now dispatch and refresh runs/audit.");

    await refreshAll();
  } catch (e) {
    setPairStatus("Not paired", false);
    setHint(`Pair failed: ${e.message}`);
  }
}

async function loadRuns() {
  try {
    const runs = await apiFetch("/v1/runs");
    const list = Array.isArray(runs)
      ? runs
      : (runs && runs.items) ? runs.items
      : (runs && runs.runs) ? runs.runs
      : [];
    state.runs = list;
    renderRuns();
  } catch (e) {
    setHint(`Runs refresh failed: ${e.message}`);
  }
}

async function loadRunDetail() {
  if (!state.currentRunId) { renderDetail(null); return; }

  try {
    const detail = await apiFetch(`/v1/runs/${encodeURIComponent(state.currentRunId)}`);
    const runObj = detail && detail.run ? { ...detail.run } : detail;
    if (detail && detail.audit && Array.isArray(detail.audit)) {
      runObj.audit = detail.audit;
    }
    renderDetail(runObj);
  } catch (e) {
    setHint(`Run detail failed: ${e.message}`);
  }
}

async function loadAudit() {
  try {
    const out = await apiFetch("/v1/audit/tail?limit=50");
    const entries = Array.isArray(out) ? out : (out && out.entries) ? out.entries : [];
    renderAudit(entries);
  } catch (e) {
    setHint(`Audit refresh failed: ${e.message}`);
  }
}

async function refreshHealth() {
  try {
    const res = await apiFetch("/v1/health");
    const ok = res && res.ok === true;
    setPill("healthPill", ok ? "Health: OK" : "Health: down", ok);
    const offline = !!(res && res.offline_mode);
    setPill("offlinePill", offline ? "Mode: Offline" : "Mode: Online", !offline);
    const url = (res && res.ui_expected) ? res.ui_expected : state.baseUrl;
    setPill("lanPill", `UI: ${url}`, true);
  } catch (e) {
    setPill("healthPill", "Health: unreachable", false);
    setHint(`Health check failed: ${e.message}`);
  }
}

async function dispatchNow() {
  const goal = prompt("Goal (what do you want SWARMZ to do)?", "status");
  if (!goal) return;

  try {
    const resp = await apiFetch("/v1/dispatch", {
      method: "POST",
      body: JSON.stringify({ goal, category: "general", constraints: {} }),
    });

    const maybeId = resp && (resp.run_id || resp.mission_id || resp.id);
    if (maybeId) state.currentRunId = maybeId;

    const offlineNote = resp && resp.run && resp.run.note;
    if (offlineNote) setHint(offlineNote);

    setHint("Dispatched. Refreshing runs/audit…");
    await refreshAll();
  } catch (e) {
    setHint(`Dispatch failed: ${e.message}`);
  }
}

async function refreshAll() {
  await Promise.allSettled([loadRuns(), loadRunDetail(), loadAudit(), refreshHealth()]);
}

function wirePwaInstall() {
  const btn = $("installBtn");
  if (!btn) return;

  window.addEventListener("beforeinstallprompt", (e) => {
    e.preventDefault();
    deferredPrompt = e;
    btn.style.display = "inline-block";
  });

  btn.addEventListener("click", async () => {
    if (!deferredPrompt) return;
    deferredPrompt.prompt();
    await deferredPrompt.userChoice;
    deferredPrompt = null;
    btn.style.display = "none";
  });
}

function registerServiceWorker() {
  if (!("serviceWorker" in navigator)) return;
  navigator.serviceWorker.register("/sw.js").catch(() => {});
}

function boot() {
  const baseUrlEl = $("baseUrl");
  if (baseUrlEl) {
    baseUrlEl.value = state.baseUrl;
    baseUrlEl.addEventListener("change", () => {
      state.baseUrl = normalizeBaseUrl(baseUrlEl.value);
      setHint(`Base URL set to ${state.baseUrl}`);
    });
  }

  $("pairBtn")?.addEventListener("click", () => pairNow());
  $("refreshInfoBtn")?.addEventListener("click", () => refreshPairingInfo());
  $("refreshRunsBtn")?.addEventListener("click", () => loadRuns());
  $("refreshDetailBtn")?.addEventListener("click", () => loadRunDetail());
  $("refreshAuditBtn")?.addEventListener("click", () => loadAudit());
  $("dispatchBtn")?.addEventListener("click", () => dispatchNow());

  if (state.token) setPairStatus("Paired", true);
  else setPairStatus("Not paired", false);

  wirePwaInstall();
  registerServiceWorker();

  loadRuntimeConfig()
    .then(() => refreshPairingInfo())
    .catch(() => refreshPairingInfo())
    .finally(() => refreshAll().catch(() => {}));
}

document.addEventListener("DOMContentLoaded", boot);
