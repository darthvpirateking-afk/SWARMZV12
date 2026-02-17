/* ═══════════════════════════════════════════════════
   SWARMZ TRIALS INBOX — trials.js
   Runtime: vanilla JS, no build step.
   ═══════════════════════════════════════════════════ */

(function () {
  'use strict';

  var API = window.location.origin;
  var POLL_MS = 5000;
  var currentTab = 'pending';
  var selectedTrialId = null;
  var pollTimer = null;

  // ── DOM refs ───────────────────────────────────
  var $errorBanner, $chipWorker, $chipTotal;
  var $tabPending, $tabNeedsReview, $tabCompleted;
  var $countPending, $countNeedsReview, $countCompleted;
  var $trialsList, $trialsDetail;
  var $btnCheckNow, $btnCreateTrial;
  var $createAction, $createContext, $createMetric;
  var $createDelay, $createDelta, $createTags, $createNotes;
  var $scoresBoard, $metricsDash;

  function el(id) { return document.getElementById(id); }

  function showError(msg) {
    if (!$errorBanner) return;
    if (!msg) { $errorBanner.classList.add('hidden'); $errorBanner.textContent = ''; return; }
    $errorBanner.textContent = msg;
    $errorBanner.classList.remove('hidden');
  }

  // ── Tab switching ──────────────────────────────

  function setTab(tab) {
    currentTab = tab;
    selectedTrialId = null;
    document.querySelectorAll('.trials-tab').forEach(function (t) {
      t.classList.toggle('active', t.getAttribute('data-tab') === tab);
    });
    fetchInbox();
    $trialsDetail.innerHTML = '<div class="empty-msg">Select a trial to view details</div>';
  }

  // ── Fetch inbox ────────────────────────────────

  async function fetchInbox() {
    try {
      var r = await fetch(API + '/v1/trials/inbox?tab=' + currentTab + '&limit=100');
      var d = await r.json();
      if (!d.ok) throw new Error(d.error || 'inbox failed');

      // Update counts
      if (d.counts) {
        $countPending.textContent = d.counts.pending || 0;
        $countNeedsReview.textContent = d.counts.needs_review || 0;
        $countCompleted.textContent = d.counts.completed || 0;
        $chipTotal.textContent = 'TOTAL ' + (d.counts.total || 0);
      }

      // Render list
      var items = d.items || [];
      if (items.length === 0) {
        $trialsList.innerHTML = '<div class="empty-msg">No trials in this tab</div>';
        return;
      }

      $trialsList.innerHTML = items.map(function (t) {
        var badge = '';
        if (t.reverted) {
          badge = '<span class="badge-survived badge-reverted">REVERTED</span>';
        } else if (t.survived === true) {
          badge = '<span class="badge-survived badge-survived-true">SURVIVED</span>';
        } else if (t.survived === false) {
          badge = '<span class="badge-survived badge-survived-false">FAILED</span>';
        } else {
          badge = '<span class="badge-survived badge-survived-pending">PENDING</span>';
        }

        var sel = t.id === selectedTrialId ? ' selected' : '';
        return '<div class="trial-row' + sel + '" data-id="' + t.id + '">'
          + '<div>'
          + '<div class="trial-action">' + esc(t.action || '--') + '</div>'
          + '<div class="trial-context">' + esc(t.context || '') + ' · ' + esc(t.metric_name || '') + '</div>'
          + '</div>'
          + '<div class="trial-metric">' + formatCheckAt(t) + '</div>'
          + badge
          + '</div>';
      }).join('');

      // Click handlers
      $trialsList.querySelectorAll('.trial-row').forEach(function (row) {
        row.addEventListener('click', function () {
          selectedTrialId = row.getAttribute('data-id');
          $trialsList.querySelectorAll('.trial-row').forEach(function (r) {
            r.classList.toggle('selected', r.getAttribute('data-id') === selectedTrialId);
          });
          fetchDetail(selectedTrialId);
        });
      });

    } catch (e) {
      showError('Inbox: ' + e.message);
    }
  }

  function formatCheckAt(t) {
    if (t.checked_at) {
      return 'checked';
    }
    if (t.check_at) {
      try {
        var d = new Date(t.check_at);
        var now = Date.now();
        var diff = d.getTime() - now;
        if (diff <= 0) return 'due now';
        var mins = Math.ceil(diff / 60000);
        if (mins < 60) return 'in ' + mins + 'm';
        return 'in ' + Math.round(mins / 60) + 'h';
      } catch (_) { return t.check_at.substring(11, 19); }
    }
    return '--';
  }

  // ── Fetch detail ───────────────────────────────

  async function fetchDetail(trialId) {
    try {
      var r = await fetch(API + '/v1/trials/detail/' + trialId);
      var d = await r.json();
      if (!d.ok) throw new Error(d.error || 'detail failed');
      renderDetail(d.trial, d.audit || []);
    } catch (e) {
      $trialsDetail.innerHTML = '<div class="empty-msg">Error: ' + esc(e.message) + '</div>';
    }
  }

  function renderDetail(t, audit) {
    var survBadge = '';
    if (t.reverted) {
      survBadge = '<span class="badge-survived badge-reverted">REVERTED</span>';
    } else if (t.survived === true) {
      survBadge = '<span class="badge-survived badge-survived-true">SURVIVED</span>';
    } else if (t.survived === false) {
      survBadge = '<span class="badge-survived badge-survived-false">FAILED</span>';
    } else {
      survBadge = '<span class="badge-survived badge-survived-pending">PENDING</span>';
    }

    var beforeVal = t.metric_before !== null && t.metric_before !== undefined ? t.metric_before : '—';
    var afterVal = t.metric_after !== null && t.metric_after !== undefined ? t.metric_after : '—';
    var afterClass = (t.survived === false) ? 'after failed' : 'after';

    var tagsHtml = (t.tags || []).map(function (tag) {
      return '<span style="background:rgba(34,211,238,0.08);padding:2px 6px;border-radius:4px;font-size:0.65rem;margin-right:4px">' + esc(tag) + '</span>';
    }).join('');

    var html = ''
      + '<div class="detail-header">'
      + '  <div class="detail-action">' + esc(t.action || '--') + ' ' + survBadge + '</div>'
      + '  <div class="detail-context">' + esc(t.context || '') + '</div>'
      + '  <div style="margin-top:4px">' + tagsHtml + '</div>'
      + '</div>'

      + '<div class="detail-arrow">'
      + '  <span class="before">' + beforeVal + '</span>'
      + '  <span class="arrow">→</span>'
      + '  <span class="' + afterClass + '">' + afterVal + '</span>'
      + '  <span style="color:rgba(255,255,255,0.3);font-size:0.7rem">(' + esc(t.metric_name || '') + ')</span>'
      + '</div>'

      + '<div class="detail-grid">'
      + '  <div class="detail-field"><div class="detail-field-label">EXPECTED Δ</div><div class="detail-field-value">' + (t.expected_delta !== null ? t.expected_delta : 'must not worsen') + '</div></div>'
      + '  <div class="detail-field"><div class="detail-field-label">CHECK DELAY</div><div class="detail-field-value">' + (t.check_after_sec || 0) + 's</div></div>'
      + '  <div class="detail-field"><div class="detail-field-label">CREATED</div><div class="detail-field-value">' + formatTs(t.created_at) + '</div></div>'
      + '  <div class="detail-field"><div class="detail-field-label">CHECK AT</div><div class="detail-field-value">' + formatTs(t.check_at) + '</div></div>'
      + '  <div class="detail-field"><div class="detail-field-label">CHECKED AT</div><div class="detail-field-value">' + formatTs(t.checked_at) + '</div></div>'
      + '  <div class="detail-field"><div class="detail-field-label">CREATED BY</div><div class="detail-field-value">' + esc(t.created_by || '') + '</div></div>'
      + '</div>';

    if (t.notes) {
      html += '<div class="detail-notes">' + esc(t.notes) + '</div>';
    }

    html += '<div class="detail-actions">';
    if (t.survived !== null && !t.reverted) {
      html += '<button class="btn btn-warn btn-tiny" onclick="trialsApp.revert(\'' + t.id + '\')">REVERT</button>';
    }
    html += '<button class="btn btn-ghost btn-tiny" onclick="trialsApp.showNoteInput(\'' + t.id + '\')">ADD NOTE</button>';
    html += '<button class="btn btn-ghost btn-tiny" onclick="trialsApp.followup(\'' + t.id + '\')">FOLLOW-UP</button>';
    html += '</div>';

    html += '<div id="noteInputContainer"></div>';

    // Audit trail
    if (audit.length > 0) {
      html += '<h3 style="font-family:var(--font-title);font-size:0.7rem;color:rgba(255,255,255,0.35);margin-top:14px;letter-spacing:0.08em">AUDIT TRAIL</h3>';
      html += '<div style="max-height:150px;overflow-y:auto">';
      audit.forEach(function (a) {
        html += '<div style="font-size:0.68rem;color:rgba(255,255,255,0.4);padding:2px 0;border-bottom:1px solid rgba(255,255,255,0.03)">'
          + formatTs(a.ts) + ' · ' + esc(a.event_type || '?')
          + '</div>';
      });
      html += '</div>';
    }

    $trialsDetail.innerHTML = html;
  }

  function formatTs(ts) {
    if (!ts) return '—';
    try {
      return ts.substring(0, 19).replace('T', ' ');
    } catch (_) { return ts; }
  }

  function esc(s) {
    if (!s) return '';
    var d = document.createElement('div');
    d.textContent = s;
    return d.innerHTML;
  }

  // ── Actions ────────────────────────────────────

  async function revertTrial(trialId) {
    try {
      var r = await fetch(API + '/v1/trials/' + trialId + '/revert', { method: 'POST' });
      var d = await r.json();
      if (!d.ok) throw new Error(d.error || 'revert failed');
      fetchInbox();
      fetchDetail(trialId);
    } catch (e) {
      showError('Revert: ' + e.message);
    }
  }

  function showNoteInput(trialId) {
    var container = document.getElementById('noteInputContainer');
    if (!container) return;
    container.innerHTML = '<div class="note-input-row">'
      + '<input type="text" id="noteText" placeholder="Add a note...">'
      + '<button class="btn btn-primary btn-tiny" onclick="trialsApp.submitNote(\'' + trialId + '\')">SAVE</button>'
      + '</div>';
    var input = document.getElementById('noteText');
    if (input) input.focus();
  }

  async function submitNote(trialId) {
    var input = document.getElementById('noteText');
    if (!input || !input.value.trim()) return;
    try {
      var r = await fetch(API + '/v1/trials/' + trialId + '/note', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ note: input.value.trim() })
      });
      var d = await r.json();
      if (!d.ok) throw new Error(d.error || 'note failed');
      fetchDetail(trialId);
    } catch (e) {
      showError('Note: ' + e.message);
    }
  }

  async function followup(trialId) {
    try {
      var r = await fetch(API + '/v1/trials/' + trialId + '/followup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({})
      });
      var d = await r.json();
      if (!d.ok) throw new Error(d.error || 'followup failed');
      setTab('pending');
    } catch (e) {
      showError('Followup: ' + e.message);
    }
  }

  async function createTrial() {
    var action = $createAction.value.trim();
    var context = $createContext.value.trim();
    var metric = $createMetric.value;
    var delay = parseInt($createDelay.value) || 300;
    var delta = $createDelta.value.trim() ? parseFloat($createDelta.value) : null;
    var tagsRaw = $createTags.value.trim();
    var tags = tagsRaw ? tagsRaw.split(',').map(function (s) { return s.trim(); }).filter(Boolean) : [];
    var notes = $createNotes.value.trim() || null;

    if (!action) { showError('Action is required'); return; }
    if (!context) { showError('Context is required'); return; }

    try {
      var r = await fetch(API + '/v1/trials/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: action,
          context: context,
          metric_name: metric,
          check_after_sec: delay,
          expected_delta: delta,
          tags: tags,
          notes: notes,
        })
      });
      var d = await r.json();
      if (!d.ok) throw new Error(d.error || 'create failed');

      // Clear form
      $createAction.value = '';
      $createContext.value = '';
      $createDelay.value = '300';
      $createDelta.value = '';
      $createTags.value = '';
      $createNotes.value = '';
      showError('');

      setTab('pending');
    } catch (e) {
      showError('Create: ' + e.message);
    }
  }

  async function checkNow() {
    try {
      var r = await fetch(API + '/v1/trials/worker/check-now', { method: 'POST' });
      var d = await r.json();
      if (!d.ok) throw new Error(d.error || 'check failed');
      fetchInbox();
    } catch (e) {
      showError('Check: ' + e.message);
    }
  }

  // ── Scores & Metrics ──────────────────────────

  async function fetchScores() {
    try {
      var r = await fetch(API + '/v1/trials/scores?limit=20');
      var d = await r.json();
      if (!d.ok || !d.scores || d.scores.length === 0) {
        $scoresBoard.innerHTML = '<div class="empty-msg">No survival scores yet</div>';
        return;
      }
      $scoresBoard.innerHTML = d.scores.map(function (s, i) {
        var pct = Math.round(s.survival_rate * 100);
        var isLow = pct < 40;
        var cls = isLow ? 'score-card low-conf' : 'score-card';
        var barCls = isLow ? 'score-bar-fill low' : 'score-bar-fill';
        return '<div class="' + cls + '">'
          + '<div class="score-template">' + esc(s.action_template || '?') + '</div>'
          + '<div class="score-tag">' + esc(s.tag || '') + '</div>'
          + '<div class="score-bar"><div class="' + barCls + '" style="width:' + pct + '%"></div></div>'
          + '<div class="score-rate">' + pct + '% survival</div>'
          + '<div class="score-counts">' + s.survived_count + ' survived / ' + s.failed_count + ' failed</div>'
          + '</div>';
      }).join('');
    } catch (_) {
      $scoresBoard.innerHTML = '<div class="empty-msg">Could not load scores</div>';
    }
  }

  async function fetchMetrics() {
    try {
      var r = await fetch(API + '/v1/trials/metrics');
      var d = await r.json();
      if (!d.ok) throw new Error(d.error || 'metrics failed');
      var metrics = d.metrics || [];
      var resolved = d.resolved || {};
      $metricsDash.innerHTML = metrics.map(function (m) {
        var val = resolved[m] ? resolved[m].value : null;
        var display = val !== null && val !== undefined ? val : '—';
        return '<div class="metric-card">'
          + '<div class="metric-name">' + esc(m) + '</div>'
          + '<div class="metric-value">' + display + '</div>'
          + '</div>';
      }).join('');
    } catch (_) {
      $metricsDash.innerHTML = '<div class="empty-msg">Could not load metrics</div>';
    }
  }

  async function fetchWorkerStatus() {
    try {
      var r = await fetch(API + '/v1/trials/worker/status');
      var d = await r.json();
      if (d.ok && d.running) {
        $chipWorker.textContent = 'WORKER UP';
        $chipWorker.className = 'chip chip-ok';
      } else {
        $chipWorker.textContent = 'WORKER DOWN';
        $chipWorker.className = 'chip chip-err';
      }
    } catch (_) {
      $chipWorker.textContent = 'WORKER --';
      $chipWorker.className = 'chip';
    }
  }

  // ── Poll ───────────────────────────────────────

  async function pollAll() {
    await fetchInbox();
    await fetchWorkerStatus();
    await fetchScores();
    await fetchMetrics();
  }

  // ── Init ───────────────────────────────────────

  function init() {
    $errorBanner = el('errorBanner');
    $chipWorker = el('chipWorker');
    $chipTotal = el('chipTotal');
    $tabPending = el('tabPending');
    $tabNeedsReview = el('tabNeedsReview');
    $tabCompleted = el('tabCompleted');
    $countPending = el('countPending');
    $countNeedsReview = el('countNeedsReview');
    $countCompleted = el('countCompleted');
    $trialsList = el('trialsList');
    $trialsDetail = el('trialsDetail');
    $btnCheckNow = el('btnCheckNow');
    $btnCreateTrial = el('btnCreateTrial');
    $createAction = el('createAction');
    $createContext = el('createContext');
    $createMetric = el('createMetric');
    $createDelay = el('createDelay');
    $createDelta = el('createDelta');
    $createTags = el('createTags');
    $createNotes = el('createNotes');
    $scoresBoard = el('scoresBoard');
    $metricsDash = el('metricsDash');

    // Wire tabs
    $tabPending.addEventListener('click', function () { setTab('pending'); });
    $tabNeedsReview.addEventListener('click', function () { setTab('needs_review'); });
    $tabCompleted.addEventListener('click', function () { setTab('completed'); });

    // Wire buttons
    $btnCheckNow.addEventListener('click', checkNow);
    $btnCreateTrial.addEventListener('click', createTrial);

    // Auto-start worker
    fetch(API + '/v1/trials/worker/start', { method: 'POST' }).catch(function () {});

    // Initial load
    pollAll();
    pollTimer = setInterval(pollAll, POLL_MS);
  }

  // Expose actions globally for inline onclick handlers
  window.trialsApp = {
    revert: revertTrial,
    showNoteInput: showNoteInput,
    submitNote: submitNote,
    followup: followup,
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();
