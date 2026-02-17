/* ═══════════════════════════════════════════════════
   SWARMZ HOLOGRAM — hologram.js
   Frontend controller. Polls /v1/hologram/state,
   renders orb + ladder + powers + currencies + burst.
   ═══════════════════════════════════════════════════ */
(function () {
  'use strict';

  const API = window.location.origin;
  const POLL_MS = 5000;

  const el = id => document.getElementById(id);
  const esc = s => String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');

  /* ── State ──────────────────────────────────────── */
  let currentLevel = 0;
  let burstEnabled = false;
  let activeBatchId = null;
  let currentTrialId = null;
  let pollTimer = null;

  /* ══════════════════════════════════════════════════
     INIT
     ══════════════════════════════════════════════════ */
  async function init() {
    await pollAll();
    pollTimer = setInterval(pollAll, POLL_MS);
  }

  async function pollAll() {
    try {
      await Promise.all([
        fetchState(),
        fetchBurstBatches(),
      ]);
      hideError();
    } catch (e) {
      showError('Hologram poll failed: ' + e.message);
    }
  }

  /* ── Error banner ──────────────────────────────── */
  function showError(msg) {
    const b = el('errorBanner');
    if (b) { b.textContent = msg; b.classList.remove('hidden'); }
  }
  function hideError() {
    const b = el('errorBanner');
    if (b) { b.classList.add('hidden'); }
  }

  /* ══════════════════════════════════════════════════
     FETCH STATE
     ══════════════════════════════════════════════════ */
  async function fetchState() {
    const resp = await fetch(API + '/v1/hologram/state');
    const data = await resp.json();
    if (!data.ok) { showError(data.error || 'State fetch failed'); return; }
    renderState(data);
  }

  function renderState(s) {
    currentLevel = s.level;
    burstEnabled = s.burst_enabled;

    // Chips
    el('chipLevel').textContent = s.label || ('LV' + s.level);
    el('chipXP').textContent = 'XP ' + s.xp;

    // Orb
    const orb = el('evoOrb');
    orb.className = 'evo-orb lv' + s.level;
    el('orbLevel').textContent = s.level;
    el('orbName').textContent = s.name;

    // XP bar
    const nextXp = s.next_level ? s.next_level.xp_needed : s.xp;
    const xpPct = nextXp > 0 ? Math.min((s.xp / nextXp) * 100, 100) : 100;
    el('barXP').style.width = xpPct + '%';
    el('valXP').textContent = s.xp + ' / ' + nextXp;

    // Currency bars
    const cur = s.currencies || {};
    el('barStab').style.width = (cur.stability * 100).toFixed(0) + '%';
    el('valStab').textContent = (cur.stability * 100).toFixed(0) + '%';
    el('barNov').style.width  = (cur.novelty * 100).toFixed(0) + '%';
    el('valNov').textContent  = (cur.novelty * 100).toFixed(0) + '%';
    el('barRev').style.width  = (cur.reversibility * 100).toFixed(0) + '%';
    el('valRev').textContent  = (cur.reversibility * 100).toFixed(0) + '%';

    // Currency cards
    el('currStab').textContent = (cur.stability * 100).toFixed(0) + '%';
    el('currNov').textContent  = (cur.novelty * 100).toFixed(0) + '%';
    el('currRev').textContent  = (cur.reversibility * 100).toFixed(0) + '%';

    // Next evolution
    if (s.next_level) {
      el('evoNext').style.display = '';
      el('nextName').textContent = s.next_level.name;
      el('nextHint').textContent = s.next_level.hint;
    } else {
      el('evoNext').style.display = 'none';
    }

    // Ladder
    renderLadder(s.level);

    // Powers
    renderPowers(s.powers || []);

    // If a specific trial is loaded, keep orb effect classes in sync
    // with its last-known effects; otherwise clear per-trial overlays.
    if (!currentTrialId) {
      clearOrbEffects();
    }

    // Burst panel visibility
    const bp = el('burstPanel');
    if (s.level >= 4) {
      bp.style.display = '';
      renderBurstState(s.burst_enabled);
    } else {
      bp.style.display = 'none';
    }

    // Drift panel visibility
    const dp = el('driftPanel');
    if (s.level >= 4) {
      dp.style.display = '';
      renderDriftEvents(s.drift_events || 0);
    } else {
      dp.style.display = 'none';
    }
  }

  /* ══════════════════════════════════════════════════
     LADDER
     ══════════════════════════════════════════════════ */
  function renderLadder(level) {
    const nodes = document.querySelectorAll('.ladder-node');
    nodes.forEach(n => {
      const lv = parseInt(n.dataset.level, 10);
      n.classList.remove('active', 'unlocked', 'locked');
      if (lv === level) n.classList.add('active');
      else if (lv < level) n.classList.add('unlocked');
      else n.classList.add('locked');
    });
  }

  /* ══════════════════════════════════════════════════
     POWERS
     ══════════════════════════════════════════════════ */
  function renderPowers(powers) {
    const container = el('powersList');
    if (!powers.length) {
      container.innerHTML = '<div class="empty-msg">No powers unlocked yet (LV0)</div>';
      return;
    }
    container.innerHTML = powers.map(p => `
      <div class="power-card">
        <span class="power-level-badge">LV${p.level}</span>
        <div class="power-info">
          <span class="power-name">${esc(p.name)}</span>
          <span class="power-desc">${esc(p.description)}</span>
        </div>
      </div>
    `).join('');
  }

  /* ══════════════════════════════════════════════════
     TRIAL LENS (PER-TRIAL EFFECTS)
     ══════════════════════════════════════════════════ */

  async function loadTrial() {
    const input = el('trialIdInput');
    if (!input) return;
    const trialId = (input.value || '').trim();
    if (!trialId) {
      showError('Enter a Trial ID from the Trials inbox.');
      return;
    }
    try {
      const resp = await fetch(API + '/v1/hologram/trial/' + encodeURIComponent(trialId));
      const data = await resp.json();
      if (!data.ok) {
        showError(data.error || 'Trial not found');
        return;
      }
      currentTrialId = trialId;
      hideError();
      renderTrialDetail(data);
    } catch (e) {
      showError('Trial load failed: ' + e.message);
    }
  }

  function renderTrialDetail(detail) {
    const box = el('trialSummary');
    if (!box) return;

    const trial = detail.trial || {};
    const verdict = detail.verdict || {};
    const effects = detail.effects || {};

    const verdictStatus = (verdict.status || 'pending').toLowerCase();
    const verdictLabel = verdict.label || verdictStatus.toUpperCase();

    const why = detail.why_failed_hint || '';

    const ctx = trial.context || '';
    const action = trial.action || '';
    const metricName = trial.metric_name || '';
    const before = trial.metric_before;
    const after = trial.metric_after;

    const glow = typeof effects.glow_intensity === 'number' ? effects.glow_intensity : 0;
    const flicker = typeof effects.flicker_rate === 'number' ? effects.flicker_rate : 0;

    box.innerHTML = `
      <div class="trial-header">
        <div>
          <div class="trial-title">${esc(action || 'Unknown action')}</div>
          <div class="trial-meta">${esc(ctx || 'no-context')} · ${esc(metricName || 'metric')}</div>
        </div>
        <span class="trial-verdict-badge ${esc(verdictStatus)}">${esc(verdictLabel)}</span>
      </div>
      <div class="trial-effects-row">
        <span><strong>Glow</strong> ${glow.toFixed(2)}</span>
        <span><strong>Flicker</strong> ${flicker.toFixed(2)}</span>
        <span><strong>Scanlines</strong> ${effects.scanlines ? 'ON' : 'off'}</span>
        <span><strong>Shimmer</strong> ${effects.field_shimmer ? 'ON' : 'off'}</span>
        <span><strong>Overclock</strong> ${effects.overclock ? 'ON' : 'off'}</span>
      </div>
      <div class="trial-effects-row">
        <span><strong>Metric</strong> ${before != null ? before : '∅'} → ${after != null ? after : '∅'}</span>
      </div>
      ${why ? `<div class="trial-why">${esc(why)}</div>` : ''}
    `;

    applyOrbEffectsFrom(effects);
  }

  /* ══════════════════════════════════════════════════
     BURST MODE
     ══════════════════════════════════════════════════ */
  function renderBurstState(enabled) {
    const status = el('burstStatus');
    const btn = el('btnBurstToggle');
    const panel = el('burstPanel');

    if (enabled) {
      status.textContent = 'ON';
      status.className = 'burst-status on';
      btn.textContent = 'DISABLE BURST';
      panel.classList.add('burst-active');
      el('btnBurstKill').disabled = false;
    } else {
      status.textContent = 'OFF';
      status.className = 'burst-status off';
      btn.textContent = 'ENABLE BURST';
      panel.classList.remove('burst-active');
      el('btnBurstKill').disabled = true;
    }
  }

  async function toggleBurst() {
    const newState = !burstEnabled;
    try {
      const resp = await fetch(API + '/v1/hologram/burst/toggle', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled: newState }),
      });
      const data = await resp.json();
      if (!data.ok) { showError(data.error); return; }
      burstEnabled = data.burst_enabled;
      renderBurstState(burstEnabled);
    } catch (e) {
      showError('Burst toggle failed: ' + e.message);
    }
  }

  async function killBatch() {
    if (!activeBatchId) { showError('No active batch to kill'); return; }
    try {
      const resp = await fetch(API + '/v1/hologram/burst/kill/' + activeBatchId, {
        method: 'POST',
      });
      const data = await resp.json();
      if (!data.ok) { showError(data.error); return; }
      await fetchBurstBatches();
    } catch (e) {
      showError('Kill failed: ' + e.message);
    }
  }

  async function fetchBurstBatches() {
    try {
      const resp = await fetch(API + '/v1/hologram/burst/batches');
      const data = await resp.json();
      if (!data.ok) return;
      renderBatches(data.batches || []);
    } catch (_) {}
  }

  function renderBatches(batches) {
    const container = el('burstBatches');
    if (!batches.length) {
      container.innerHTML = '<div class="empty-msg">No burst batches</div>';
      activeBatchId = null;
      return;
    }
    // Most recent first
    const reversed = [...batches].reverse();
    activeBatchId = reversed[0].batch_id;
    container.innerHTML = reversed.map(b => `
      <div class="batch-card">
        <span class="batch-id">${esc(b.batch_id.substring(0, 8))}...</span>
        <span class="batch-count">${b.trial_count} trials</span>
        <button class="batch-kill-btn" onclick="holoApp.killSpecificBatch('${esc(b.batch_id)}')">KILL</button>
      </div>
    `).join('');
  }

  async function killSpecificBatch(batchId) {
    try {
      const resp = await fetch(API + '/v1/hologram/burst/kill/' + batchId, {
        method: 'POST',
      });
      const data = await resp.json();
      if (!data.ok) { showError(data.error); return; }
      await fetchBurstBatches();
    } catch (e) {
      showError('Kill failed: ' + e.message);
    }
  }

  /* ══════════════════════════════════════════════════
     DRIFT EVENTS
     ══════════════════════════════════════════════════ */
  function renderDriftEvents(count) {
    const container = el('driftEvents');
    if (count === 0) {
      container.innerHTML = '<div class="empty-msg">No drift events recorded</div>';
      return;
    }
    // We show count; full detail via API call if needed
    container.innerHTML = `
      <div class="drift-card">
        <span class="drift-metric">Total drift events</span>
        <span class="drift-mag">${count}</span>
        <span class="drift-ts">Tracked by hologram engine</span>
      </div>
    `;
  }

  /* ══════════════════════════════════════════════════
     ORB EFFECT HELPERS
     ══════════════════════════════════════════════════ */

  function clearOrbEffects() {
    const orb = el('evoOrb');
    if (!orb) return;
    orb.classList.remove('effect-flicker', 'effect-shimmer', 'effect-overclock', 'effect-glow-weak', 'effect-glow-strong');
  }

  function applyOrbEffectsFrom(effects) {
    const orb = el('evoOrb');
    if (!orb) return;

    clearOrbEffects();

    const glow = typeof effects.glow_intensity === 'number' ? effects.glow_intensity : 0;
    const flicker = typeof effects.flicker_rate === 'number' ? effects.flicker_rate : 0;

    if (glow > 0.15 && glow <= 0.6) {
      orb.classList.add('effect-glow-weak');
    } else if (glow > 0.6) {
      orb.classList.add('effect-glow-strong');
    }

    if (flicker > 0.0) {
      orb.classList.add('effect-flicker');
    }
    if (effects.field_shimmer) {
      orb.classList.add('effect-shimmer');
    }
    if (effects.overclock) {
      orb.classList.add('effect-overclock');
    }
  }

  /* ══════════════════════════════════════════════════
     GLOBAL API (for onclick handlers)
     ══════════════════════════════════════════════════ */
  window.holoApp = {
    toggleBurst,
    killBatch,
    killSpecificBatch,
    loadTrial,
    refresh: pollAll,
  };

  /* Start */
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
