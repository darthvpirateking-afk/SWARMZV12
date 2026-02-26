/**
 * NEXUSMON Console - Conversational Interface for NEXUSMON
 *
 * Web component for chat-based interaction with the NEXUSMON system.
 * Integrates persona, evolution state, and system health into conversation.
 */

// Import-style module pattern for compatibility

const NexusmonConsole = (() => {
  const MAX_ASSISTANT_TEXT = 1200;

  // State
  let state = {
    operatorId: null,
    messages: [],
    loading: false,
    snapshot: null,
    currentScreen: 'None',
    currentMissionId: null,
    apiBase: '/v1/nexusmon',
    ws: null,
    wsConnected: false
  };

  // DOM references
  let elements = {};

  /**
   * Initialize NEXUSMON Console
   */
  async function init(operatorId, options = {}) {
    state.operatorId = operatorId;
    state.apiBase = options.apiBase || '/v1/nexusmon';
    state.currentScreen = options.screen || 'None';
    state.currentMissionId = options.missionId || null;

    elements.container = document.getElementById('nexusmon-console');
    if (!elements.container) {
      console.error('NEXUSMON: Container #nexusmon-console not found');
      return;
    }

    renderUI();
    await loadOperatorProfile();
    await loadNexusForm();
  }

  /**
   * Render the UI
   */
  function renderUI() {
    elements.container.innerHTML = `
      <div class="nexusmon-console">
        <div class="nexusmon-header">
          <div class="header-left">
            <h2>NEXUSMON</h2>
            <div id="nexus-form" class="nexus-form-badge">Loading...</div>
          </div>
          <div class="header-right">
            <div id="system-health" class="system-health">
              <span id="entropy">E:--</span>
              <span id="coherence">C:--</span>
              <span id="missions">M:--</span>
            </div>
          </div>
        </div>

        <div class="nexusmon-messages" id="messages-container">
          <!-- Messages will be inserted here -->
        </div>

        <div class="nexusmon-input">
          <input
            type="text"
            id="chat-input"
            placeholder="Tell NEXUSMON what's on your mind..."
            disabled
          />
          <button id="send-btn" disabled>Send</button>
          <span id="loading-indicator" class="loading" style="display:none;">⟳</span>
        </div>

        <div class="nexusmon-actions" id="actions-container">
          <!-- Suggested actions will appear here -->
        </div>

        <div class="nexusmon-footer">
          <small>NEXUSMON v1.0 | Evolutionary Companion | Operator-Sovereign Design</small>
        </div>
      </div>
    `;

    // Store references
    elements.input = document.getElementById('chat-input');
    elements.sendBtn = document.getElementById('send-btn');
    elements.messagesContainer = document.getElementById('messages-container');
    elements.actionsContainer = document.getElementById('actions-container');
    elements.nexusFormBadge = document.getElementById('nexus-form');
    elements.entropySpan = document.getElementById('entropy');
    elements.coherenceSpan = document.getElementById('coherence');
    elements.missionsSpan = document.getElementById('missions');
    elements.loadingIndicator = document.getElementById('loading-indicator');

    // Enable input and button
    elements.input.disabled = false;
    elements.sendBtn.disabled = false;

    // Event listeners
    elements.sendBtn.addEventListener('click', sendMessage);
    elements.input.addEventListener('keypress', e => {
      if (e.key === 'Enter' && !state.loading) {
        sendMessage();
      }
    });

    injectStyles();
  }

  /**
   * Inject CSS styles
   */
  function injectStyles() {
    if (document.getElementById('nexusmon-styles')) return;

    const style = document.createElement('style');
    style.id = 'nexusmon-styles';
    style.textContent = `
      .nexusmon-console {
        display: flex;
        flex-direction: column;
        height: 100%;
        background: #0d1117;
        color: #c9d1d9;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 2px 12px rgba(0, 0, 0, 0.3);
      }

      .nexusmon-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 16px;
        background: linear-gradient(135deg, #161b22 0%, #0d1117 100%);
        border-bottom: 1px solid #30363d;
      }

      .header-left h2 {
        margin: 0;
        font-size: 18px;
        font-weight: 600;
        color: #58a6ff;
      }

      .nexus-form-badge {
        margin-top: 4px;
        font-size: 12px;
        color: #8b949e;
        font-weight: 500;
      }

      .nexus-form-badge.operator { color: #79c0ff; }
      .nexus-form-badge.cosmology { color: #d29922; }
      .nexus-form-badge.overseer { color: #f85149; }
      .nexus-form-badge.sovereign { color: #a371f7; }

      .system-health {
        display: flex;
        gap: 12px;
        font-size: 12px;
        color: #8b949e;
      }

      .system-health span {
        padding: 4px 8px;
        background: #161b22;
        border-radius: 4px;
      }

      .nexusmon-messages {
        flex: 1;
        overflow-y: auto;
        padding: 16px;
        display: flex;
        flex-direction: column;
        gap: 12px;
      }

      .message {
        display: flex;
        gap: 8px;
        animation: slideIn 0.3s ease-out;
      }

      @keyframes slideIn {
        from {
          opacity: 0;
          transform: translateY(8px);
        }
        to {
          opacity: 1;
          transform: translateY(0);
        }
      }

      .message.user {
        justify-content: flex-end;
      }

      .message-bubble {
        max-width: 70%;
        padding: 12px;
        border-radius: 8px;
        word-wrap: break-word;
      }

      .message-bubble.collapsed {
        max-height: 280px;
        overflow: hidden;
        position: relative;
      }

      .message-bubble.collapsed::after {
        content: '';
        position: absolute;
        left: 0;
        right: 0;
        bottom: 0;
        height: 38px;
        background: linear-gradient(to bottom, rgba(13, 17, 23, 0), rgba(13, 17, 23, 0.95));
        pointer-events: none;
      }

      .message-expand-btn {
        margin-top: 6px;
        background: transparent;
        border: 1px solid #30363d;
        color: #58a6ff;
        border-radius: 4px;
        font-size: 11px;
        padding: 4px 8px;
        cursor: pointer;
      }

      .message-expand-btn:hover {
        border-color: #58a6ff;
        background: #0d1117;
      }

      .message.user .message-bubble {
        background: #238636;
        color: white;
        border-bottom-right-radius: 2px;
      }

      .message.assistant .message-bubble {
        background: #161b22;
        border: 1px solid #30363d;
        border-bottom-left-radius: 2px;
      }

      .message.system-event {
        justify-content: center;
      }

      .message.system-event .message-bubble {
        max-width: 90%;
        background: rgba(0, 170, 255, 0.06);
        border: 1px solid rgba(0, 170, 255, 0.25);
        border-radius: 6px;
        color: #00AAFF;
        font-size: 12px;
        font-style: italic;
        text-align: center;
        padding: 8px 14px;
      }

      .message.error .message-bubble {
        background: rgba(239, 68, 68, 0.08);
        border: 1px solid rgba(239, 68, 68, 0.3);
        color: #EF4444;
        font-size: 12px;
      }

      .artifact-section {
        margin-top: 10px;
        padding-top: 8px;
        border-top: 1px solid #30363d;
      }

      .artifact-section:first-child {
        margin-top: 0;
        padding-top: 0;
        border-top: none;
      }

      .artifact-label {
        font-size: 11px;
        color: #8b949e;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        margin-bottom: 4px;
      }

      .artifact-value {
        font-size: 13px;
        white-space: pre-wrap;
        word-break: break-word;
      }

      .artifact-list {
        margin: 0;
        padding-left: 18px;
      }

      .artifact-list li {
        margin: 2px 0;
      }

      .message-mode {
        font-size: 11px;
        color: #8b949e;
        margin-top: 4px;
        text-align: right;
      }

      .message.assistant .message-mode {
        text-align: left;
      }

      .nexusmon-input {
        display: flex;
        gap: 8px;
        padding: 12px;
        background: #161b22;
        border-top: 1px solid #30363d;
      }

      #chat-input {
        flex: 1;
        padding: 10px 12px;
        border: 1px solid #30363d;
        background: #0d1117;
        color: #c9d1d9;
        border-radius: 6px;
        font-size: 14px;
      }

      #chat-input:focus {
        outline: none;
        border-color: #58a6ff;
        box-shadow: 0 0 0 2px rgba(88, 166, 255, 0.1);
      }

      #send-btn {
        padding: 10px 16px;
        background: #238636;
        color: white;
        border: none;
        border-radius: 6px;
        cursor: pointer;
        font-weight: 500;
        transition: background 0.2s;
      }

      #send-btn:hover:not(:disabled) {
        background: #2ea043;
      }

      #send-btn:disabled {
        opacity: 0.5;
        cursor: not-allowed;
      }

      .loading {
        display: inline-block;
        animation: spin 1s infinite linear;
      }

      @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
      }

      .nexusmon-actions {
        padding: 12px;
        background: #161b22;
        border-top: 1px solid #30363d;
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
      }

      .action-btn {
        padding: 8px 12px;
        background: #0d1117;
        border: 1px solid #30363d;
        color: #58a6ff;
        border-radius: 4px;
        cursor: pointer;
        font-size: 12px;
        transition: all 0.2s;
      }

      .action-btn:hover {
        background: #161b22;
        border-color: #58a6ff;
      }

      .nexusmon-footer {
        padding: 8px 12px;
        background: #0d1117;
        border-top: 1px solid #30363d;
        text-align: center;
        color: #8b949e;
        font-size: 11px;
      }
    `;

    document.head.appendChild(style);
  }

  /**
   * Load operator profile
   */
  async function loadOperatorProfile() {
    try {
      const res = await fetch(`${state.apiBase}/operators/${state.operatorId}/profile`);
      const profile = await res.json();
      // Profile loaded, can be used for context
      console.log('Operator profile:', profile);
    } catch (err) {
      console.error('Error loading operator profile:', err);
    }
  }

  /**
   * Load NexusForm and update UI
   */
  async function loadNexusForm() {
    try {
      const res = await fetch(`${state.apiBase}/operators/${state.operatorId}/nexus-form`);
      const form = await res.json();

      const formValue = form.current_form || 'Operator';
      const formClass = formValue.toLowerCase();

      elements.nexusFormBadge.textContent = `${formValue} Form`;
      elements.nexusFormBadge.className = `nexus-form-badge ${formClass}`;
    } catch (err) {
      console.error('Error loading NexusForm:', err);
    }
  }

  /**
   * Send a message to NEXUSMON
   */
  async function sendMessage() {
    const message = elements.input.value.trim();
    if (!message || state.loading) return;

    // Add user message to UI
    addMessageToUI(message, 'user');

    // Clear input
    elements.input.value = '';
    elements.input.disabled = true;
    elements.sendBtn.disabled = true;
    elements.loadingIndicator.style.display = 'inline-block';

    state.loading = true;

    // ── WebSocket path ─────────────────────────────────────────────
    if (state.wsConnected && state.ws && state.ws.readyState === WebSocket.OPEN) {
      state.ws.send(JSON.stringify({
        type: 'chat',
        operator_id: state.operatorId,
        message: message,
        screen: state.currentScreen,
        mission_id: state.currentMissionId
      }));
      // Loading state is reset by _finishLoading() called from the WS message handler
      return;
    }

    // ── HTTP fallback ──────────────────────────────────────────────
    try {
      // Send to backend
      const res = await fetch(`${state.apiBase}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          operator_id: state.operatorId,
          message: message,
          context: {
            mission_id: state.currentMissionId,
            screen: state.currentScreen
          }
        })
      });

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }

      const reply = await res.json();

      // Add assistant message to UI
      addMessageToUI(reply.reply, 'assistant', reply.mode);

      // Update state snapshot
      if (reply.state_snapshot) {
        updateStateSnapshot(reply.state_snapshot);
      }

      // Show suggested actions
      if (reply.suggested_actions && reply.suggested_actions.length > 0) {
        showSuggestedActions(reply.suggested_actions);
      }

      // Store message in state
      state.messages.push({
        role: 'user',
        content: message
      });
      state.messages.push({
        role: 'assistant',
        content: reply.reply,
        mode: reply.mode
      });

    } catch (err) {
      console.error('Error sending message:', err);
      addMessageToUI(`Error: ${err.message}`, 'error');
    } finally {
      _finishLoading();
    }
  }

  /**
   * Add a message to the UI
   */
  function addMessageToUI(text, role, mode = null) {
    const messageEl = document.createElement('div');
    messageEl.className = `message ${role}`;

    const bubbleEl = document.createElement('div');
    bubbleEl.className = 'message-bubble';

    if (role === 'assistant') {
      renderAssistantContent(bubbleEl, text);
      applyAssistantCollapse(messageEl, bubbleEl, text);
    } else {
      bubbleEl.textContent = text;
    }

    messageEl.appendChild(bubbleEl);

    if (mode && role === 'assistant') {
      const modeEl = document.createElement('div');
      modeEl.className = 'message-mode';
      modeEl.textContent = `[${mode}]`;
      messageEl.appendChild(modeEl);
    }

    elements.messagesContainer.appendChild(messageEl);
    elements.messagesContainer.scrollTop = elements.messagesContainer.scrollHeight;
  }

  function applyAssistantCollapse(messageEl, bubbleEl, text) {
    if (!text || text.length <= MAX_ASSISTANT_TEXT) {
      return;
    }

    bubbleEl.classList.add('collapsed');
    const toggle = document.createElement('button');
    toggle.className = 'message-expand-btn';
    toggle.textContent = 'Show more';
    toggle.addEventListener('click', () => {
      const isCollapsed = bubbleEl.classList.toggle('collapsed');
      toggle.textContent = isCollapsed ? 'Show more' : 'Show less';
      elements.messagesContainer.scrollTop = elements.messagesContainer.scrollHeight;
    });
    messageEl.appendChild(toggle);
  }

  function renderAssistantContent(container, text) {
    const parsed = parseArtifactContract(text);
    if (!parsed) {
      container.textContent = text;
      return;
    }

    if (parsed.modeTag) {
      const modeLine = document.createElement('div');
      modeLine.className = 'artifact-section';
      modeLine.appendChild(makeLabel('mode'));
      modeLine.appendChild(makeValue(parsed.modeTag));
      container.appendChild(modeLine);
    }

    if (parsed.artifact) {
      const artifactLine = document.createElement('div');
      artifactLine.className = 'artifact-section';
      artifactLine.appendChild(makeLabel('artifact'));
      artifactLine.appendChild(makeValue(parsed.artifact));
      container.appendChild(artifactLine);
    }

    if (parsed.works) {
      const worksLine = document.createElement('div');
      worksLine.className = 'artifact-section';
      worksLine.appendChild(makeLabel('works'));
      worksLine.appendChild(makeValue(parsed.works));
      container.appendChild(worksLine);
    }

    if (parsed.applied) {
      const appliedLine = document.createElement('div');
      appliedLine.className = 'artifact-section';
      appliedLine.appendChild(makeLabel('applied'));
      appliedLine.appendChild(makeValue(parsed.applied));
      container.appendChild(appliedLine);
    }

    if (parsed.whatElse.length) {
      const whatElseLine = document.createElement('div');
      whatElseLine.className = 'artifact-section';
      whatElseLine.appendChild(makeLabel('what_else'));
      const list = document.createElement('ul');
      list.className = 'artifact-list';
      parsed.whatElse.forEach(item => {
        const li = document.createElement('li');
        li.textContent = item;
        list.appendChild(li);
      });
      whatElseLine.appendChild(list);
      container.appendChild(whatElseLine);
    }

    if (parsed.analysis) {
      const analysisLine = document.createElement('div');
      analysisLine.className = 'artifact-section';
      analysisLine.appendChild(makeLabel('analysis'));
      analysisLine.appendChild(makeValue(parsed.analysis));
      container.appendChild(analysisLine);
    }
  }

  function makeLabel(text) {
    const el = document.createElement('div');
    el.className = 'artifact-label';
    el.textContent = text;
    return el;
  }

  function makeValue(text) {
    const el = document.createElement('div');
    el.className = 'artifact-value';
    el.textContent = text;
    return el;
  }

  function parseArtifactContract(text) {
    if (typeof text !== 'string' || !text.includes('artifact:') || !text.includes('works:')) {
      return null;
    }

    const modeMatch = text.match(/^\[([^\]]+)\]/);
    const artifactMatch = text.match(/artifact:\n([\s\S]*?)\n\nworks:/);
    const worksMatch = text.match(/\nworks:\s*([^\n]+)/);
    const appliedMatch = text.match(/\napplied:\s*([^\n]+)/);
    const whatElseMatch = text.match(/\nwhat_else:\n([\s\S]*?)\n\nanalysis:/);
    const analysisMatch = text.match(/\nanalysis:\n([\s\S]*)$/);

    if (!artifactMatch || !worksMatch) {
      return null;
    }

    const whatElse = whatElseMatch
      ? whatElseMatch[1]
          .split('\n')
          .map(line => line.trim())
          .filter(line => line.startsWith('- '))
          .map(line => line.slice(2).trim())
      : [];

    return {
      modeTag: modeMatch ? modeMatch[1] : '',
      artifact: artifactMatch[1].trim(),
      works: worksMatch[1].trim(),
      applied: appliedMatch ? appliedMatch[1].trim() : '',
      whatElse,
      analysis: analysisMatch ? analysisMatch[1].trim() : ''
    };
  }

  /**
   * Update state snapshot in UI
   */
  function updateStateSnapshot(snapshot) {
    state.snapshot = snapshot;

    if (snapshot.system_health) {
      const h = snapshot.system_health;
      elements.entropySpan.textContent = `E:${(h.entropy * 100).toFixed(0)}%`;
      elements.coherenceSpan.textContent = `C:${(h.coherence * 100).toFixed(0)}%`;
    }

    if (snapshot.active_missions !== undefined) {
      elements.missionsSpan.textContent = `M:${snapshot.active_missions}`;
    }
  }

  /**
   * Show suggested actions
   */
  function showSuggestedActions(actions) {
    elements.actionsContainer.innerHTML = '';

    actions.forEach(action => {
      const btn = document.createElement('button');
      btn.className = 'action-btn';
      btn.textContent = formatActionLabel(action.type);
      btn.addEventListener('click', () => handleAction(action));
      elements.actionsContainer.appendChild(btn);
    });
  }

  /**
   * Format action type to human-readable label
   */
  function formatActionLabel(type) {
    const labels = {
      'OpenMission': '📂 Open Mission',
      'CreateMission': '✨ Create Mission',
      'ViewShadow': '👁 View Shadow',
      'ViewMetrics': '📊 View Metrics',
      'ViewAudit': '📜 View Audit'
    };
    return labels[type] || type;
  }

  /**
   * Re-enable input after a reply (shared by WS and HTTP paths)
   */
  function _finishLoading() {
    state.loading = false;
    elements.input.disabled = false;
    elements.sendBtn.disabled = false;
    elements.loadingIndicator.style.display = 'none';
    elements.input.focus();
  }

  /**
   * Handle incoming WebSocket message
   */
  function _handleWsMessage(msg) {
    switch (msg.type) {
      // Legacy connected frame
      case 'connected':
        console.log('[NEXUSMON WS]', msg.message);
        break;

      // New character-aware greeting on connect
      case 'greeting':
        if (msg.text) {
          addMessageToUI(msg.text, 'assistant');
        }
        if (msg.entity) {
          _dispatchEntityEvent(msg.entity);
        }
        break;

      case 'thinking':
        break;

      case 'reply':
        addMessageToUI(msg.reply, 'assistant', msg.mode);

        // New entity payload (Phase 1+)
        if (msg.entity) {
          _dispatchEntityEvent(msg.entity);
        }
        // Operator profile update
        if (msg.operator) {
          _dispatchOperatorEvent(msg.operator);
        }
        // Legacy state_snapshot (HTTP path, old WS format)
        if (msg.state_snapshot) {
          updateStateSnapshot(msg.state_snapshot);
        }
        if (msg.suggested_actions && msg.suggested_actions.length > 0) {
          showSuggestedActions(msg.suggested_actions);
        }

        state.messages.push({ role: 'assistant', content: msg.reply, mode: msg.mode });
        _finishLoading();
        break;

      // Evolution event — Nexusmon grows
      case 'evolution':
        addMessageToUI(
          msg.message || `NEXUSMON evolved: ${msg.from} -> ${msg.to}`,
          'system-event'
        );
        if (msg.entity) {
          _dispatchEntityEvent(msg.entity);
        }
        break;

      case 'error':
        addMessageToUI(`Error: ${msg.message}`, 'error');
        _finishLoading();
        break;

      case 'pong':
        break;

      default:
        console.warn('[NEXUSMON WS] Unknown message type:', msg.type);
    }
  }

  /**
   * Dispatch a custom event so the cockpit HTML script can update the left panel.
   */
  function _dispatchEntityEvent(entity) {
    const el = document.getElementById('nexusmon-console');
    if (el) {
      el.dispatchEvent(new CustomEvent('nexusmon:entity', { detail: entity, bubbles: true }));
    }
  }

  function _dispatchOperatorEvent(operator) {
    const el = document.getElementById('nexusmon-console');
    if (el) {
      el.dispatchEvent(new CustomEvent('nexusmon:operator', { detail: operator, bubbles: true }));
    }
  }

  /**
   * Open a WebSocket connection. Falls back to HTTP automatically if WS fails.
   */
  function connectWebSocket(url) {
    const wsUrl = url || `ws://${location.host}/ws/nexusmon`;
    try {
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        state.ws = ws;
        state.wsConnected = true;
        console.log('[NEXUSMON WS] Connected to', wsUrl);
        ws.send(JSON.stringify({ type: 'ping' }));
      };

      ws.onmessage = (event) => {
        try {
          _handleWsMessage(JSON.parse(event.data));
        } catch (e) {
          console.error('[NEXUSMON WS] Parse error:', e);
        }
      };

      ws.onclose = () => {
        state.wsConnected = false;
        state.ws = null;
        console.log('[NEXUSMON WS] Disconnected — falling back to HTTP');
      };

      ws.onerror = () => {
        state.wsConnected = false;
        state.ws = null;
        console.warn('[NEXUSMON WS] Connection failed — HTTP fallback active');
      };
    } catch (e) {
      console.warn('[NEXUSMON WS] WebSocket not available:', e);
    }
  }

  /**
   * Handle suggested action click
   */
  function handleAction(action) {
    console.log('Action clicked:', action);
    // Dispatch custom event or call callback
    const event = new CustomEvent('nexusmon:action', { detail: action });
    elements.container.dispatchEvent(event);
  }

  /**
   * Public API
   */
  return {
    init,
    sendMessage: () => sendMessage(),
    addMessage: (text, role) => addMessageToUI(text, role),
    loadProfile: loadOperatorProfile,
    loadForm: loadNexusForm,
    connectWebSocket
  };
})();

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
  module.exports = NexusmonConsole;
}

