/* ═══════════════════════════════════════════════════
   NEXUSMON CONTROL — app.js
   Runtime: vanilla JS, no build step.
   ═══════════════════════════════════════════════════ */

(function () {
  'use strict';

  // ── Constants ──────────────────────────────────
  var API = window.location.origin;
  var POLL_MS = 2000;

  // ── State ──────────────────────────────────────
  var connected = false;
  var currentMode = 'COMPANION';
  var operatorKey = localStorage.getItem('nexusmon_opkey') || '';
  var currentMissionId = localStorage.getItem('nexusmon_cur_mission') || '';
  var pollTimer = null;

  // ── DOM refs ───────────────────────────────────
  var $chipRuntime, $chipState, $chipLan, $chipLock, $chipAi, $chipView;
  var $errorBanner, $quarantineBanner;
  var $opKeyInput, $goalInput;
  var $tabCompanion, $tabBuild, $tabHologram;
  var $companionView, $buildView, $hologramView;
  var $companionInput, $companionReply, $btnSend;
  var $intentInput, $specInput, $btnDispatch, $btnCommit;
  var $btnSync, $btnResetShell;
  var $actionHint, $panelTitle;
  var $statTotal, $statPending, $statSuccess, $statRunning;
  var $missionList, $currentMission;
  var $guidanceSummary, $networkSummary;
  var $infraSummary, $infraAutoscale, $infraBackup;
  var $btnInfraSim;
  var $logFeed;

  // ── Soft state for guidance ───────────────────
  var viewMode = localStorage.getItem('nexusmon_view_mode') || 'CLOSE';
  var operatorGoal = localStorage.getItem('nexusmon_goal') || '';
  var lastUiState = null;
  var lastMissions = [];
  var lastInfraOverview = null;
  var lastAutoscale = null;
  var lastBackup = null;
  var lastAiStatus = null;

  // ── Helpers ────────────────────────────────────
  function el(id) { return document.getElementById(id); }

  function authHeaders() {
    var h = { 'Content-Type': 'application/json' };
    if (operatorKey) h['x-operator-key'] = operatorKey;
    return h;
  }

  function showError(msg) {
    if (!$errorBanner) return;
    if (!msg) { $errorBanner.classList.add('hidden'); $errorBanner.textContent = ''; return; }
    $errorBanner.textContent = msg;
    $errorBanner.classList.remove('hidden');
  }

  function setChip(elem, text, cls) {
    if (!elem) return;
    elem.textContent = text;
    elem.className = 'chip' + (cls ? ' ' + cls : '');
  }

  function hint(msg) { if ($actionHint) $actionHint.textContent = msg || ''; }

  function persistKey() {
    if ($opKeyInput) {
      operatorKey = $opKeyInput.value.trim();
      localStorage.setItem('nexusmon_opkey', operatorKey);
      updateLockChip();
    }
  }

  function persistGoal() {
    if ($goalInput) {
      operatorGoal = $goalInput.value.trim();
      localStorage.setItem('nexusmon_goal', operatorGoal);
      computeGuidance();
      updateNetworkSummary();
    }
  }

  function updateViewChip() {
    if (!$chipView) return;
    var label = viewMode === 'FAR' ? 'VIEW FAR' : 'VIEW CLOSE';
    $chipView.textContent = label;
    $chipView.className = 'chip chip-clickable chip-dim';
  }

  function updateLockChip() {
    if (!$chipLock) return;
    if (operatorKey) {
      setChip($chipLock, 'UNLOCKED', 'chip-unlock');
    } else {
      setChip($chipLock, 'LOCKED', 'chip-lock');
    }
  }

  // ── Mode switching ─────────────────────────────

  function setMode(mode) {
    currentMode = mode;
    // tabs
    if ($tabCompanion) $tabCompanion.classList.toggle('active', mode === 'COMPANION');
    if ($tabBuild) $tabBuild.classList.toggle('active', mode === 'BUILD');
    if ($tabHologram) $tabHologram.classList.toggle('active', mode === 'HOLOGRAM');
    // views
    if (mode === 'COMPANION') {
      if ($companionView) $companionView.classList.remove('hidden');
      if ($buildView) $buildView.classList.add('hidden');
      if ($hologramView) $hologramView.classList.add('hidden');
      if ($panelTitle) $panelTitle.textContent = 'COMPANION';
    } else if (mode === 'BUILD') {
      if ($companionView) $companionView.classList.add('hidden');
      if ($buildView) $buildView.classList.remove('hidden');
      if ($hologramView) $hologramView.classList.add('hidden');
      if ($panelTitle) $panelTitle.textContent = 'DISPATCH';
    } else if (mode === 'HOLOGRAM') {
      if ($companionView) $companionView.classList.add('hidden');
      if ($buildView) $buildView.classList.add('hidden');
      if ($hologramView) {
        $hologramView.classList.remove('hidden');
        // lazy-load hologram iframe
        var iframe = document.getElementById('hologramFrame');
        if (iframe && !iframe.src) {
          iframe.src = '/hologram';
          iframe.style.display = 'block';
          var placeholder = $hologramView.querySelector('.empty-msg');
          if (placeholder) placeholder.style.display = 'none';
        }
      }
      if ($panelTitle) $panelTitle.textContent = 'HOLOGRAM';
    }
  }

  async function switchModeServer(mode) {
    persistKey();
    try {
      var r = await fetch(API + '/v1/mode', {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify({ mode: mode })
      });
      var d = await r.json();
      if (!r.ok || !d.ok) throw new Error(d.error || d.detail || 'mode switch failed');
      setMode(d.mode);
    } catch (e) {
      showError('Mode: ' + e.message);
    }
  }

  // ── API calls ──────────────────────────────────

  async function checkHealth() {
    try {
      var r = await fetch(API + '/health');
      var d = await r.json();
      if (d && d.status === 'ok') {
        connected = true;
        setChip($chipRuntime, 'RUNTIME UP', 'chip-ok');
      } else { throw new Error('bad'); }
    } catch (_) {
      connected = false;
      setChip($chipRuntime, 'RUNTIME DOWN', 'chip-err');
    }
  }

  async function fetchMode() {
    try {
      var r = await fetch(API + '/v1/mode', { headers: authHeaders() });
      var d = await r.json();
      if (d && d.ok) setMode(d.mode);
    } catch (_) { /* ignore */ }
  }

  async function fetchUiState() {
    try {
      var r = await fetch(API + '/v1/ui/state', { headers: authHeaders() });
      var d = await r.json();
      if (!d || !d.ok) throw new Error(d.error || 'ui/state failed');

      // phase
      setChip($chipState, 'STATE ' + (d.phase || '--'));

      // LAN url
      if (d.server && d.server.lan_url) {
        setChip($chipLan, 'LAN ' + d.server.lan_url, 'chip-dim');
      }

      // stats
      if (d.missions) {
        $statTotal.textContent   = d.missions.count_total || 0;
        var s = d.missions.count_by_status || {};
        $statPending.textContent = s.PENDING || 0;
        $statSuccess.textContent = s.SUCCESS || 0;
        $statRunning.textContent = s.RUNNING || 0;
      }

      // system log
      if (d.last_events && d.last_events.length) {
        $logFeed.innerHTML = d.last_events.map(function (e) {
          return '<div>' + (e.timestamp || '') + ' \u00b7 ' + (e.event || '?') + '</div>';
        }).join('');
        $logFeed.scrollTop = $logFeed.scrollHeight;
      }

      lastUiState = d;
      computeGuidance();
      showError('');
    } catch (e) {
      if (connected) showError('State: ' + e.message);
    }
  }

  async function fetchAiStatus() {
    try {
      var r = await fetch(API + '/v1/ai/status', { headers: authHeaders() });
      var d = await r.json();
      if (!d || !d.ok) throw new Error('ai/status failed');

      // AI chip
      if (d.offlineMode) {
        setChip($chipAi, 'AI OFFLINE', 'chip-ai-off');
      } else if (d.apiKeySet) {
        setChip($chipAi, 'AI ' + (d.provider || '').toUpperCase() + ':' + (d.model || '').substring(0, 16), 'chip-ai-on');
      } else {
        setChip($chipAi, 'AI NO KEY', 'chip-ai-off');
      }

      // QUARANTINE banner
      if (d.quarantine) {
        $quarantineBanner.classList.remove('hidden');
      } else {
        $quarantineBanner.classList.add('hidden');
      }
    } catch (_) {
      setChip($chipAi, 'AI --', 'chip-ai-off');
      lastAiStatus = null;
      computeGuidance();
    }
  }

  async function fetchInfra() {
    if (!$infraSummary) return;
    try {
      var rOverview = await fetch(API + '/v1/infra/overview', { headers: authHeaders() });
      if (rOverview.status === 404) {
        $infraSummary.textContent = 'INFRA: DISABLED';
        $infraAutoscale.textContent = 'AUTOSCALE: --';
        $infraBackup.textContent = 'BACKUP: --';
        lastInfraOverview = null;
        lastAutoscale = null;
        lastBackup = null;
        computeGuidance();
        updateNetworkSummary();
        return;
      }
      var overview = await rOverview.json();
      var nodes = (overview && overview.nodes) ? overview.nodes.length : 0;
      $infraSummary.textContent = 'INFRA: ' + nodes + ' node' + (nodes === 1 ? '' : 's');
      lastInfraOverview = overview;

      var rAuto = await fetch(API + '/v1/infra/autoscale_plan', { headers: authHeaders() });
      var autoscale;
      if (rAuto.status !== 404) {
        autoscale = await rAuto.json();
        var s = (autoscale && autoscale.summary) || {};
        $infraAutoscale.textContent = 'AUTOSCALE: ' + (s.status || 'n/a');
        lastAutoscale = autoscale;
      } else {
        $infraAutoscale.textContent = 'AUTOSCALE: --';
        lastAutoscale = null;
      }

      var rBackup = await fetch(API + '/v1/infra/backup_plan', { headers: authHeaders() });
      if (rBackup.status !== 404) {
        var backup = await rBackup.json();
        var bsum = (backup && backup.summary) || {};
        $infraBackup.textContent = 'BACKUP: ' + (bsum.status || 'n/a');
        lastBackup = backup;
      } else {
        $infraBackup.textContent = 'BACKUP: --';
        lastBackup = null;
      }

      computeGuidance();
      updateNetworkSummary();
    } catch (_) {
      // Fail soft: leave last-known values in place.
    }
  }

  async function fetchMissions() {
    try {
      var r = await fetch(API + '/v1/missions/list', { headers: authHeaders() });
      var d = await r.json();
      if (!d || !d.ok) throw new Error(d.error || 'missions/list failed');

      var missions = d.missions || [];
      if (missions.length === 0) {
        $missionList.innerHTML = '<div class="empty-msg">NO MISSIONS YET</div>';
      } else {
        $missionList.innerHTML = missions.map(function (m) {
          var isActive = m.mission_id === currentMissionId;
          return '<div class="mission-row' + (isActive ? ' active' : '') + '" data-id="' + m.mission_id + '">'
            + '<span class="mission-id">' + (m.mission_id || '').substring(0, 12) + '</span>'
            + '<span class="mission-goal">' + (m.goal || m.intent || '--').substring(0, 40) + '</span>'
            + '<span class="badge badge-' + (m.status || 'PENDING') + '">' + (m.status || '?') + '</span>'
            + '</div>';
        }).join('');

        $missionList.querySelectorAll('.mission-row').forEach(function (row) {
          row.addEventListener('click', function () {
            currentMissionId = row.getAttribute('data-id');
            localStorage.setItem('nexusmon_cur_mission', currentMissionId);
            refreshMissionSelection(missions);
          });
        });
      }
      lastMissions = missions;
      refreshMissionSelection(missions);
      computeGuidance();
      updateNetworkSummary();
    } catch (e) {
      if (connected) showError('Missions: ' + e.message);
    }
  }

  // ── Contextual guidance ───────────────────────

  function computeGuidance() {
    if (!$guidanceSummary) return;

    if (!connected) {
      $guidanceSummary.textContent = 'Waiting for runtime...';
      return;
    }

    var pending = 0;
    for (var i = 0; i < lastMissions.length; i++) {
      if ((lastMissions[i].status || 'PENDING') === 'PENDING') pending++;
    }

    var hasInfra = !!lastInfraOverview;
    var autoscaleStatus = lastAutoscale && lastAutoscale.summary && lastAutoscale.summary.status;

    var aiOffline = false;
    if (lastAiStatus && lastAiStatus.offlineMode) aiOffline = true;

    var base;
    if (viewMode === 'FAR') {
      base = 'FAR MODE · '; // system-scale focus
    } else {
      base = 'CLOSE MODE · '; // hand-scale focus
    }

    if (viewMode === 'CLOSE') {
      if (pending > 0) {
        $guidanceSummary.textContent = base + 'Review and commit one of ' + pending + ' pending missions.';
        return;
      }
      if (hasInfra && autoscaleStatus && autoscaleStatus !== 'normal') {
        $guidanceSummary.textContent = base + 'Infra shows "' + autoscaleStatus + '" — consider running an INFRA SIM.';
        return;
      }
      if (aiOffline) {
        $guidanceSummary.textContent = base + 'AI offline — set an API key to unlock full capability.';
        return;
      }
      if (operatorGoal) {
        $guidanceSummary.textContent = base + 'Goal: ' + operatorGoal;
      } else {
        $guidanceSummary.textContent = base + 'System steady. Define a new INTENT or companion query.';
      }
    } else {
      var nodes = (lastInfraOverview && lastInfraOverview.nodes) ? lastInfraOverview.nodes.length : 0;
      var total = (lastUiState && lastUiState.missions && lastUiState.missions.count_total) || lastMissions.length || 0;
      var msg = base + 'Missions: ' + total + ' total, ' + pending + ' pending';
      if (hasInfra) {
        msg += ' · Infra nodes: ' + nodes;
        if (autoscaleStatus) msg += ' · Autoscale: ' + autoscaleStatus;
      }
      if (aiOffline) msg += ' · AI OFFLINE';
      if (operatorGoal) msg += ' · Goal: ' + operatorGoal;
      $guidanceSummary.textContent = msg;
    }
  }

  function updateNetworkSummary() {
    if (!$networkSummary) return;

    if (!connected) {
      $networkSummary.textContent = 'NETWORK: WAITING';
      return;
    }

    if (!lastInfraOverview || !lastInfraOverview.nodes || !lastInfraOverview.nodes.length) {
      $networkSummary.textContent = 'NETWORK: NO INFRA DATA';
      return;
    }

    var nodes = lastInfraOverview.nodes;
    var count = nodes.length;
    var autoscaleStatus = lastAutoscale && lastAutoscale.summary && lastAutoscale.summary.status;

    var cohesion = 'COHERENT';
    if (autoscaleStatus && autoscaleStatus !== 'normal') cohesion = 'SHIFTING';

    var label = 'NETWORK: ' + count + ' node' + (count === 1 ? '' : 's') + ' · ' + cohesion;
    if (operatorGoal) label += ' · Goal: ' + operatorGoal;
    $networkSummary.textContent = label;
  }

  function refreshMissionSelection(missions) {
    $missionList.querySelectorAll('.mission-row').forEach(function (row) {
      row.classList.toggle('active', row.getAttribute('data-id') === currentMissionId);
    });
    var cur = null;
    for (var i = 0; i < missions.length; i++) {
      if (missions[i].mission_id === currentMissionId) { cur = missions[i]; break; }
    }
    if (cur) {
      $currentMission.innerHTML =
        '<strong>' + cur.mission_id + '</strong><br>' +
        (cur.goal || cur.intent || '--') + '<br>' +
        '<span class="badge badge-' + cur.status + '">' + cur.status + '</span>' +
        (cur.created_at || cur.timestamp ? ' \u00b7 ' + (cur.created_at || cur.timestamp) : '');
    } else {
      $currentMission.innerHTML = '<span style="opacity:0.3">No mission selected</span>';
    }
  }

  // ── Actions ────────────────────────────────────

  async function sendCompanion() {
    var text = $companionInput.value.trim();
    if (!text) { hint('Enter a message.'); return; }
    persistKey();
    hint('Sending...');
    try {
      var r = await fetch(API + '/v1/companion/message', {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify({ text: text })
      });
      var d = await r.json();
      if (!r.ok || !d.ok) throw new Error(d.error || d.detail || 'companion failed');
      var sourceTag = d.source ? ' [' + d.source + ']' : '';
      $companionReply.textContent = (d.reply || '(empty)') + sourceTag;
      $companionInput.value = '';
      hint('');
    } catch (e) {
      showError('Companion: ' + e.message);
      hint('');
    }
  }

  async function dispatchBuild() {
    var intent = $intentInput.value.trim();
    if (!intent) { hint('Enter an intent.'); return; }
    var spec = {};
    if ($specInput.value.trim()) {
      try { spec = JSON.parse($specInput.value.trim()); } catch (_) { hint('Invalid JSON spec.'); return; }
    }
    persistKey();
    hint('Dispatching...');
    try {
      var r = await fetch(API + '/v1/build/dispatch', {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify({ intent: intent, spec: spec })
      });
      var d = await r.json();
      if (!r.ok || !d.ok) throw new Error(d.error || d.detail || 'dispatch failed');
      currentMissionId = d.mission_id;
      localStorage.setItem('nexusmon_cur_mission', currentMissionId);
      $intentInput.value = '';
      $specInput.value = '';
      hint('Dispatched: ' + d.mission_id);
      pollNow();
    } catch (e) {
      showError('Dispatch: ' + e.message);
      hint('');
    }
  }

  async function commitMission() {
    if (!currentMissionId) { hint('Select a mission first.'); return; }
    persistKey();
    hint('Committing...');
    try {
      var r = await fetch(API + '/v1/missions/run?mission_id=' + encodeURIComponent(currentMissionId), {
        method: 'POST',
        headers: authHeaders()
      });
      var d = await r.json();
      if (!r.ok || !d.ok) throw new Error(d.error || d.detail || 'commit failed');
      hint('Committed: ' + currentMissionId);
      pollNow();
    } catch (e) {
      showError('Commit: ' + e.message);
      hint('');
    }
  }

  async function runInfraSimulation() {
    if (!$infraSummary) return;
    persistKey();
    hint('Planning infra missions...');
    try {
      var r = await fetch(API + '/v1/infra/plan_missions', {
        method: 'POST',
        headers: authHeaders()
      });
      if (r.status === 404) {
        hint('INFRA orchestrator disabled.');
        return;
      }
      var d = await r.json();
      if (!d || d.ok === false) {
        throw new Error((d && (d.error || d.detail)) || 'plan_missions failed');
      }
      var created = d.created_missions || 0;
      hint('Infra sim: created ' + created + ' mission' + (created === 1 ? '' : 's') + '.');
      // Refresh missions so new entries show up in the queue.
      pollNow();
    } catch (e) {
      showError('Infra sim: ' + e.message);
      hint('');
    }
  }

  async function resetShell() {
    hint('Resetting shell...');
    try {
      if ('serviceWorker' in navigator) {
        var regs = await navigator.serviceWorker.getRegistrations();
        for (var i = 0; i < regs.length; i++) { await regs[i].unregister(); }
      }
      if (window.caches) {
        var keys = await caches.keys();
        for (var j = 0; j < keys.length; j++) { await caches.delete(keys[j]); }
      }
      hint('Shell cleared. Reloading...');
      location.reload(true);
    } catch (e) {
      showError('Reset shell: ' + e.message);
    }
  }

  // ── Poll loop ──────────────────────────────────

  async function pollNow() {
    await checkHealth();
    await Promise.all([fetchUiState(), fetchMissions(), fetchAiStatus(), fetchInfra()]);
  }

  function startPolling() {
    if (pollTimer) clearInterval(pollTimer);
    pollNow();
    pollTimer = setInterval(pollNow, POLL_MS);
  }

  // ── Service Worker ─────────────────────────────

  function registerSW() {
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('/pwa/sw.js').catch(function () {});
    }
  }

  // ── Init ───────────────────────────────────────

  function init() {
    $chipRuntime    = el('chipRuntime');
    $chipState      = el('chipState');
    $chipLan        = el('chipLan');
    $chipLock       = el('chipLock');
    $chipView       = el('chipView');
    $chipAi         = el('chipAi');
    $errorBanner    = el('errorBanner');
    $quarantineBanner = el('quarantineBanner');
    $opKeyInput     = el('opKeyInput');
    $goalInput      = el('goalInput');
    $tabCompanion   = el('tabCompanion');
    $tabBuild       = el('tabBuild');
    $tabHologram    = el('tabHologram');
    $companionView  = el('companionView');
    $buildView      = el('buildView');
    $hologramView  = el('hologramView');
    $companionInput = el('companionInput');
    $companionReply = el('companionReply');
    $btnSend        = el('btnSend');
    $intentInput    = el('intentInput');
    $specInput      = el('specInput');
    $btnDispatch    = el('btnDispatch');
    $btnCommit      = el('btnCommit');
    $btnSync        = el('btnSync');
    $btnResetShell  = el('btnResetShell');
    $actionHint     = el('actionHint');
    $panelTitle     = el('panelTitle');
    $statTotal      = el('statTotal');
    $statPending    = el('statPending');
    $statSuccess    = el('statSuccess');
    $statRunning    = el('statRunning');
    $missionList    = el('missionList');
    $currentMission = el('currentMission');
    $guidanceSummary = el('guidanceSummary');
    $logFeed        = el('logFeed');
    $infraSummary   = el('infraSummary');
    $infraAutoscale = el('infraAutoscale');
    $infraBackup    = el('infraBackup');
    $networkSummary = el('networkSummary');
    $btnInfraSim    = el('btnInfraSim');

    // restore operator key
    if ($opKeyInput && operatorKey) $opKeyInput.value = operatorKey;
    if ($goalInput && operatorGoal) $goalInput.value = operatorGoal;
    updateLockChip();
    updateViewChip();

    // wire mode tabs
    if ($tabCompanion) $tabCompanion.addEventListener('click', function () { switchModeServer('COMPANION'); });
    if ($tabBuild) $tabBuild.addEventListener('click', function () { switchModeServer('BUILD'); });
    if ($tabHologram) $tabHologram.addEventListener('click', function () { switchModeServer('HOLOGRAM'); });

    // wire buttons
    if ($btnSend) $btnSend.addEventListener('click', sendCompanion);
    if ($btnDispatch) $btnDispatch.addEventListener('click', dispatchBuild);
    if ($btnCommit) $btnCommit.addEventListener('click', commitMission);
    if ($btnSync) $btnSync.addEventListener('click', function () { pollNow(); });
    if ($btnResetShell) $btnResetShell.addEventListener('click', resetShell);
    if ($chipView) {
      $chipView.addEventListener('click', function () {
        viewMode = viewMode === 'FAR' ? 'CLOSE' : 'FAR';
        localStorage.setItem('nexusmon_view_mode', viewMode);
        updateViewChip();
        computeGuidance();
      });
    }
    if ($btnInfraSim) {
      $btnInfraSim.addEventListener('click', runInfraSimulation);
    }

    // save key on blur
    if ($opKeyInput) $opKeyInput.addEventListener('blur', persistKey);
    if ($companionInput) {
      $companionInput.addEventListener('keydown', function (ev) {
        if (ev.key === 'Enter') { sendCompanion(); }
      });
    }
    if ($goalInput) {
      $goalInput.addEventListener('blur', persistGoal);
      $goalInput.addEventListener('keydown', function (ev) {
        if (ev.key === 'Enter') {
          persistGoal();
        }
      });
    }

    // init mode from server
    fetchMode();

    // go
    registerSW();
    startPolling();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();

