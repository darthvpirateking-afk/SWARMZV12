const state = {
  baseUrl: window.location.origin,
  token: localStorage.getItem("nexusmon_token") || "",
  runs: [],
  currentRunId: null,
  offlineMode: false,
};

let deferredPrompt = null;

const commandCatalog = [
  "help",
  "health",
  "runs",
  "audit",
  "command-center",
  "dispatch",
  "pair",
  "clear",
];

let audioCtx = null;

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

function ensureAudioCtx() {
  if (audioCtx || !window.AudioContext) return;
  audioCtx = new AudioContext();
}

function playUiTone(type = "ok") {
  try {
    ensureAudioCtx();
    if (!audioCtx) return;
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.type = "sine";
    osc.frequency.value = type === "error" ? 180 : type === "dispatch" ? 520 : 420;
    gain.gain.value = 0.0001;
    osc.connect(gain);
    gain.connect(audioCtx.destination);
    const now = audioCtx.currentTime;
    gain.gain.exponentialRampToValueAtTime(0.03, now + 0.015);
    gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.12);
    osc.start(now);
    osc.stop(now + 0.14);
  } catch {}
}

function vibratePattern(type = "ok") {
  if (!navigator.vibrate) return;
  if (type === "error") navigator.vibrate([20, 30, 30]);
  else if (type === "dispatch") navigator.vibrate([15, 25, 15]);
  else navigator.vibrate(12);
}

function systemFeel(type = "ok") {
  playUiTone(type);
  vibratePattern(type);
}

function escapeHtml(s) {
  return String(s)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function appendConsoleLine(message) {
  const box = $("consoleOutput");
  if (!box) return;
  const line = `[${new Date().toLocaleTimeString()}] ${message}`;
  box.innerHTML = `${box.innerHTML}\n${escapeHtml(line)}`;
  box.scrollTop = box.scrollHeight;
}

function highlightCommand(input) {
  const preview = $("consolePreview");
  if (!preview) return;
  const src = (input || "").trim();
  if (!src) {
    preview.textContent = "Awaiting input…";
    return;
  }
  const pieces = src.split(/\s+/);
  const rootCommand = (pieces[0] || "").toLowerCase();
  const tokens = pieces.map((token, index) => {
    let cls = "token-keyword";
    if (/^--/.test(token)) cls = "token-flag";
    else if (/^[0-9]+$/.test(token)) cls = "token-number";
    else if ((token.startsWith('"') && token.endsWith('"')) || (token.startsWith("'") && token.endsWith("'"))) cls = "token-string";
    else if (index > 0 && commandCatalog.includes(rootCommand)) cls = "token-string";
    return `<span class="token ${cls}">${escapeHtml(token)}</span>`;
  });
  preview.innerHTML = tokens.join(" ");
}

function updateAutocomplete(input) {
  const box = $("consoleAutocomplete");
  if (!box) return;
  const value = (input || "").trim().toLowerCase();
  const matches = value
    ? commandCatalog.filter((cmd) => cmd.startsWith(value)).slice(0, 6)
    : commandCatalog.slice(0, 6);
  box.innerHTML = "";
  for (const cmd of matches) {
    const chip = document.createElement("button");
    chip.type = "button";
    chip.className = "suggestion-chip";
    chip.textContent = cmd;
    chip.addEventListener("click", () => {
      const prompt = $("consolePrompt");
      if (!prompt) return;
      prompt.value = cmd + " ";
      prompt.focus();
      highlightCommand(prompt.value);
      updateAutocomplete(prompt.value);
    });
    box.appendChild(chip);
  }
}

function renderCommandCenterOutput(payload) {
  const box = $("commandCenterOutput");
  if (!box) return;
  if (!payload) {
    box.textContent = "Command center state unavailable.";
    return;
  }
  box.textContent = JSON.stringify(payload, null, 2);
}

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
    localStorage.setItem("nexusmon_token", token);
    setPairStatus("Paired", true);
    setHint("Token stored. Ignition controls activated - operator sovereignty engaged.");
    showIgnitionControls();
    showCommandCenterControls();

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
  const goal = prompt("Goal (what do you want NEXUSMON to do)?", "status");
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
    systemFeel("dispatch");
    await refreshAll();
  } catch (e) {
    systemFeel("error");
    setHint(`Dispatch failed: ${e.message}`);
  }
}

async function runConsolePrompt() {
  const prompt = $("consolePrompt");
  const raw = (prompt?.value || "").trim();
  if (!raw) return;

  appendConsoleLine(`> ${raw}`);
  const [command, ...rest] = raw.split(/\s+/);
  const argText = rest.join(" ");

  try {
    switch (command.toLowerCase()) {
      case "help":
        appendConsoleLine("Commands: help, health, runs, audit, command-center, dispatch <goal>, pair <pin>, clear");
        break;
      case "health":
        await refreshHealth();
        appendConsoleLine("Health refreshed.");
        break;
      case "runs":
        await loadRuns();
        appendConsoleLine("Runs refreshed.");
        break;
      case "audit":
        await loadAudit();
        appendConsoleLine("Audit refreshed.");
        break;
      case "command-center":
        await loadCommandCenterState();
        appendConsoleLine("Command center state refreshed.");
        break;
      case "dispatch": {
        const goal = argText || "status";
        const resp = await apiFetch("/v1/dispatch", {
          method: "POST",
          body: JSON.stringify({ goal, category: "general", constraints: {} }),
        });
        appendConsoleLine(`Dispatched: ${(resp && (resp.run_id || resp.mission_id || resp.id)) || "ok"}`);
        await refreshAll();
        break;
      }
      case "pair": {
        if (!argText) {
          appendConsoleLine("Usage: pair <pin>");
          break;
        }
        const pinInput = $("pinInput");
        if (pinInput) pinInput.value = argText;
        await pairNow();
        appendConsoleLine("Pair command executed.");
        break;
      }
      case "clear": {
        const box = $("consoleOutput");
        if (box) box.innerHTML = "NEXUSMON console cleared.";
        break;
      }
      default:
        appendConsoleLine(`Unknown command: ${command}`);
        appendConsoleLine("Type help for available commands.");
        systemFeel("error");
        return;
    }
    systemFeel("ok");
  } catch (e) {
    appendConsoleLine(`ERROR: ${e.message}`);
    systemFeel("error");
  }
}

function wireConsolePrompt() {
  const prompt = $("consolePrompt");
  if (!prompt) return;

  prompt.addEventListener("input", () => {
    highlightCommand(prompt.value);
    updateAutocomplete(prompt.value);
  });

  prompt.addEventListener("keydown", async (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      await runConsolePrompt();
      return;
    }
    if (event.key === "Tab") {
      const raw = prompt.value.trim().toLowerCase();
      const match = commandCatalog.find((cmd) => cmd.startsWith(raw));
      if (match) {
        event.preventDefault();
        prompt.value = `${match} `;
        highlightCommand(prompt.value);
        updateAutocomplete(prompt.value);
      }
    }
  });

  $("consoleRunBtn")?.addEventListener("click", () => runConsolePrompt());
  $("consoleClearBtn")?.addEventListener("click", () => {
    const box = $("consoleOutput");
    if (box) box.innerHTML = "NEXUSMON console cleared.";
    if (prompt) prompt.value = "";
    highlightCommand("");
    updateAutocomplete("");
  });

  highlightCommand("");
  updateAutocomplete("");
}

async function refreshAll() {
  await Promise.allSettled([loadRuns(), loadRunDetail(), loadAudit(), refreshHealth(), loadCommandCenterState()]);
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

// Ignition control functions
function showIgnitionControls() {
  const section = $("ignitionSection");
  if (section) section.style.display = "block";
  setPill("ignitionStatus", "Active", true);
}

function hideIgnitionControls() {
  const section = $("ignitionSection");
  if (section) section.style.display = "none";
  setPill("ignitionStatus", "Inactive", false);
}

async function executeOperatorCommand() {
  const command = $("operatorCommand")?.value;
  if (!command) return;

  const params = {};

  if (command === "execute_artifact") {
    const artifactId = $("artifactId")?.value?.trim();
    if (!artifactId) {
      setHint("Artifact ID required for execution");
      return;
    }
    params.artifact_id = artifactId;
  }

  try {
    let endpoint = "/v1/admin/command";
    let body = { command, parameters: params, operator_key: state.token };

    if (command === "kernel_validate") {
      endpoint = "/v1/verify/kernel";
      body = { strict: true };
    }

    const resp = await apiFetch(endpoint, {
      method: "POST",
      body: JSON.stringify(body),
    });

    setHint(`Command executed: ${command}`);
    console.log("Command result:", resp);

    // Refresh status after command
    await refreshHealth();

  } catch (e) {
    setHint(`Command failed: ${e.message}`);
  }
}

async function validateKernel() {
  try {
    const resp = await apiFetch("/v1/verify/kernel", {
      method: "POST",
      body: JSON.stringify({ strict: true }),
    });

    const passed = resp.integrity_passed;
    setHint(passed ? "Kernel validation passed" : `Kernel issues: ${resp.issues.join(", ")}`);
    setPill("ignitionStatus", passed ? "Kernel OK" : "Kernel Issues", passed);

  } catch (e) {
    setHint(`Kernel validation failed: ${e.message}`);
    setPill("ignitionStatus", "Validation Error", false);
  }
}

function updateCommandFields() {
  const command = $("operatorCommand")?.value;
  const artifactField = $("artifactField");

  if (command === "execute_artifact") {
    if (artifactField) artifactField.style.display = "block";
  } else {
    if (artifactField) artifactField.style.display = "none";
  }
}

// Meta-selector functions
function showMetaControls() {
  const section = $("metaSection");
  if (section) section.style.display = "block";
  setPill("metaStatus", "Active", true);
}

function hideMetaControls() {
  const section = $("metaSection");
  if (section) section.style.display = "none";
  setPill("metaStatus", "Inactive", false);
}

async function makeSovereignDecision() {
  const contextText = $("decisionContext")?.value?.trim();
  const optionsText = $("decisionOptions")?.value?.trim();

  if (!contextText || !optionsText) {
    setHint("Both context and options are required for sovereign decision");
    return;
  }

  try {
    const context = JSON.parse(contextText);
    const options = JSON.parse(optionsText);

    const resp = await apiFetch("/v1/meta/decide", {
      method: "POST",
      body: JSON.stringify({ context, options }),
    });

    setHint(`Sovereign decision made: ${resp.sovereign_decision.id} (coherence: ${resp.meta_coherence.toFixed(4)})`);
    console.log("Sovereign decision:", resp);

  } catch (e) {
    setHint(`Sovereign decision failed: ${e.message}`);
  }
}

async function applySovereignControl() {
  const contextText = $("decisionContext")?.value?.trim();

  if (!contextText) {
    setHint("Context is required for sovereign control");
    return;
  }

  try {
    const context = JSON.parse(contextText);

    const resp = await apiFetch("/v1/meta/control", {
      method: "POST",
      body: JSON.stringify({ context, decision_type: "sovereign_override" }),
    });

    setHint(`Sovereign control applied: ${resp.control_decision.id}`);
    console.log("Sovereign control:", resp);

  } catch (e) {
    setHint(`Sovereign control failed: ${e.message}`);
  }
}

async function checkLatticeStatus() {
  try {
    const resp = await apiFetch("/v1/meta/lattice", {
      method: "GET",
    });

    setHint(`Lattice status: ${resp.sovereign_governance} | ${resp.lattice_layers.length} layers active`);
    console.log("Lattice status:", resp);

  } catch (e) {
    setHint(`Lattice status check failed: ${e.message}`);
  }
}

async function processTaskMatrix() {
  const contextText = $("taskContext")?.value?.trim();
  const optionsText = $("taskOptions")?.value?.trim();

  if (!contextText || !optionsText) {
    setHint("Both context and options are required for task matrix processing");
    return;
  }

  try {
    const context = JSON.parse(contextText);
    const options = JSON.parse(optionsText);

    const resp = await apiFetch("/v1/meta/task-matrix", {
      method: "POST",
      body: JSON.stringify({ context, options }),
    });

    setHint(`Task matrix processed: ${resp.ignition_state_vector.cockpit_signal.operational_readiness} (coherence: ${resp.meta_coherence.toFixed(4)})`);
    console.log("Task matrix result:", resp);

    // Auto-populate kernel ignition input
    const ignitionInput = $("ignitionStateInput");
    if (ignitionInput) {
      ignitionInput.value = JSON.stringify(resp.ignition_state_vector, null, 2);
      setHint(`Task matrix processed and ignition state loaded for kernel ignition`);
    }

  } catch (e) {
    setHint(`Task matrix processing failed: ${e.message}`);
  }
}

async function getIgnitionStatus() {
  try {
    const resp = await apiFetch("/v1/meta/ignition-status", {
      method: "GET",
    });

    setHint(`Ignition status: ${resp.ignition_phase} | Task matrix: ${resp.task_matrix} | Sovereign: ${resp.sovereign_arbitration}`);
    console.log("Ignition status:", resp);

  } catch (e) {
    setHint(`Ignition status check failed: ${e.message}`);
  }
}

async function executeKernelIgnition() {
  const ignitionStateText = $("ignitionStateInput")?.value?.trim();

  if (!ignitionStateText) {
    setHint("Ignition state vector is required for kernel ignition");
    return;
  }

  try {
    const ignitionState = JSON.parse(ignitionStateText);

    const resp = await apiFetch("/v1/meta/kernel-ignition", {
      method: "POST",
      body: JSON.stringify({ ignition_state: ignitionState }),
    });

    const kernelState = resp.ignition_result.kernel_state;
    const cockpitActivated = resp.cockpit_activated;
    const operatorControl = resp.operator_control;

    setHint(`Kernel ignition: ${kernelState} | Cockpit: ${cockpitActivated ? 'ACTIVATED' : 'STANDBY'} | Control: ${operatorControl}`);
    setPill("kernelIgnitionStatus", kernelState, kernelState === "IGNITION_COMPLETE");

    console.log("Kernel ignition result:", resp);

  } catch (e) {
    setHint(`Kernel ignition failed: ${e.message}`);
  }
}

function showTaskMatrixControls() {
  const section = $("taskMatrixSection");
  if (section) section.style.display = "block";
  setPill("taskMatrixStatus", "Active", true);
}

function hideTaskMatrixControls() {
  const section = $("taskMatrixSection");
  if (section) section.style.display = "none";
  setPill("taskMatrixStatus", "Inactive", false);
}

function showKernelIgnitionControls() {
  const section = $("kernelIgnitionSection");
  if (section) section.style.display = "block";
  setPill("kernelIgnitionStatus", "Standby", false);
}

function hideKernelIgnitionControls() {
  const section = $("kernelIgnitionSection");
  if (section) section.style.display = "none";
  setPill("kernelIgnitionStatus", "Inactive", false);
}

function showCommandCenterControls() {
  const section = $("commandCenterSection");
  if (section) section.style.display = "block";
  setPill("commandCenterStatus", "Active", true);
}

function hideCommandCenterControls() {
  const section = $("commandCenterSection");
  if (section) section.style.display = "none";
  setPill("commandCenterStatus", "Inactive", false);
}

async function loadCommandCenterState() {
  try {
    const data = await apiFetch("/v1/command-center/state");
    renderCommandCenterOutput(data);
    const autonomy = data && data.autonomy ? data.autonomy : {};
    const levelInput = $("autonomyLevelInput");
    if (levelInput && autonomy.level !== undefined) {
      levelInput.value = autonomy.level;
    }
  } catch (e) {
    renderCommandCenterOutput({ ok: false, error: e.message });
  }
}

async function setAutonomyDial() {
  const input = $("autonomyLevelInput");
  const level = Number(input?.value ?? 35);
  if (Number.isNaN(level) || level < 0 || level > 100) {
    setHint("Autonomy level must be between 0 and 100.");
    return;
  }
  try {
    const out = await apiFetch("/v1/command-center/autonomy", {
      method: "POST",
      body: JSON.stringify({ level }),
    });
    setHint(`Autonomy updated to ${out.autonomy.level} (${out.autonomy.mode}).`);
    await loadCommandCenterState();
  } catch (e) {
    setHint(`Autonomy update failed: ${e.message}`);
  }
}

async function setShadowMode() {
  const enabled = $("shadowEnabledSelect")?.value === "true";
  const lane = ($("shadowLaneInput")?.value || "mirror").trim() || "mirror";
  try {
    const out = await apiFetch("/v1/command-center/shadow", {
      method: "POST",
      body: JSON.stringify({ enabled, lane }),
    });
    setHint(`Shadow mode ${out.shadow_mode.enabled ? "enabled" : "disabled"} on lane ${out.shadow_mode.lane}.`);
    await loadCommandCenterState();
  } catch (e) {
    setHint(`Shadow mode update failed: ${e.message}`);
  }
}

async function promotePartner() {
  const partnerId = ($("promotePartnerInput")?.value || "").trim();
  if (!partnerId) {
    setHint("Enter partner_id to promote.");
    return;
  }
  try {
    const out = await apiFetch("/v1/command-center/evolution/promote", {
      method: "POST",
      body: JSON.stringify({ partner_id: partnerId, reason: "manual_console_promote" }),
    });
    setHint(`Partner ${out.partner.partner_id} promoted to ${out.partner.tier}.`);
    await loadCommandCenterState();
  } catch (e) {
    setHint(`Evolution promotion failed: ${e.message}`);
  }
}

async function publishMarketplaceListing() {
  const missionType = ($("listingTypeInput")?.value || "").trim();
  const title = ($("listingTitleInput")?.value || "").trim();
  const rewardPoints = Number($("listingRewardInput")?.value || 0);
  if (!missionType || !title) {
    setHint("Mission type and listing title are required.");
    return;
  }
  try {
    const out = await apiFetch("/v1/command-center/marketplace/publish", {
      method: "POST",
      body: JSON.stringify({
        mission_type: missionType,
        title,
        reward_points: Math.max(0, rewardPoints),
        tags: ["operator"],
      }),
    });
    setHint(`Marketplace listing created: ${out.listing.listing_id}.`);
    await loadCommandCenterState();
  } catch (e) {
    setHint(`Marketplace publish failed: ${e.message}`);
  }
}

async function loadMarketplace() {
  try {
    const out = await apiFetch("/v1/command-center/marketplace/list");
    renderCommandCenterOutput(out);
    setHint(`Marketplace loaded (${out.count} listings).`);
  } catch (e) {
    setHint(`Marketplace load failed: ${e.message}`);
  }
}

function clearIgnitionState() {
  const input = $("ignitionStateInput");
  if (input) input.value = "";
  setHint("Ignition state cleared");
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

  // Ignition controls
  $("executeCommandBtn")?.addEventListener("click", () => executeOperatorCommand());
  $("validateKernelBtn")?.addEventListener("click", () => validateKernel());
  $("operatorCommand")?.addEventListener("change", () => updateCommandFields());

  // Meta-selector controls
  $("makeSovereignDecisionBtn")?.addEventListener("click", () => makeSovereignDecision());
  $("applySovereignControlBtn")?.addEventListener("click", () => applySovereignControl());
  $("checkLatticeStatusBtn")?.addEventListener("click", () => checkLatticeStatus());

  // Task matrix controls
  $("processTaskMatrixBtn")?.addEventListener("click", () => processTaskMatrix());
  $("getIgnitionStatusBtn")?.addEventListener("click", () => getIgnitionStatus());

  // Kernel ignition controls
  $("executeKernelIgnitionBtn")?.addEventListener("click", () => executeKernelIgnition());
  $("clearIgnitionStateBtn")?.addEventListener("click", () => clearIgnitionState());

  // Command center controls
  $("refreshCommandCenterBtn")?.addEventListener("click", () => loadCommandCenterState());
  $("setAutonomyBtn")?.addEventListener("click", () => setAutonomyDial());
  $("setShadowModeBtn")?.addEventListener("click", () => setShadowMode());
  $("promotePartnerBtn")?.addEventListener("click", () => promotePartner());
  $("publishListingBtn")?.addEventListener("click", () => publishMarketplaceListing());
  $("loadMarketplaceBtn")?.addEventListener("click", () => loadMarketplace());

  if (state.token) {
    setPairStatus("Paired", true);
    showIgnitionControls();
    showMetaControls();
    showTaskMatrixControls();
    showKernelIgnitionControls();
    showCommandCenterControls();
  } else {
    setPairStatus("Not paired", false);
    hideIgnitionControls();
    hideMetaControls();
    hideTaskMatrixControls();
    hideKernelIgnitionControls();
    hideCommandCenterControls();
  }

  wirePwaInstall();
  registerServiceWorker();
  wireConsolePrompt();

  loadRuntimeConfig()
    .then(() => refreshPairingInfo())
    .catch(() => refreshPairingInfo())
    .finally(() => refreshAll().catch(() => {}));
}

document.addEventListener("DOMContentLoaded", boot);

