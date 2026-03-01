/**
 * hologram-client.esm.js
 * Hologram live-state WebSocket client with HTTP snapshot fallback.
 *
 * Usage:
 *   import createHologramClient from './hologram-client.esm.js';
 *   const client = createHologramClient({ onSnapshot, onDiff, onConnect, onDisconnect, onError });
 *   client.connect();
 *   // later:
 *   client.disconnect();
 */

import { getCanonicalCockpitBridge } from './canonical_bridge.js';

const CANONICAL_BRIDGE = getCanonicalCockpitBridge();
const DEFAULT_SNAPSHOT_URL = CANONICAL_BRIDGE.cockpit.hologramSnapshot;
const DEFAULT_WS_URL = CANONICAL_BRIDGE.cockpit.hologramWs;
const RECONNECT_BASE_MS = 1000;
const RECONNECT_MAX_MS = 30000;
const RECONNECT_FACTOR = 2;

export default function createHologramClient({
  snapshotUrl = DEFAULT_SNAPSHOT_URL,
  wsUrl = DEFAULT_WS_URL,
  onSnapshot = null,
  onDiff = null,
  onConnect = null,
  onDisconnect = null,
  onError = null,
} = {}) {
  let ws = null;
  let reconnectDelay = RECONNECT_BASE_MS;
  let reconnectTimer = null;
  let stopped = false;

  function emit(fn, ...args) {
    if (typeof fn === 'function') {
      try { fn(...args); } catch (e) { console.error('[hologram-client] callback error', e); }
    }
  }

  async function fetchSnapshot() {
    try {
      const res = await fetch(snapshotUrl);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const snap = await res.json();
      emit(onSnapshot, snap);
    } catch (err) {
      emit(onError, err);
    }
  }

  function scheduleReconnect() {
    if (stopped) return;
    reconnectTimer = setTimeout(() => {
      if (!stopped) openWs();
    }, reconnectDelay);
    reconnectDelay = Math.min(reconnectDelay * RECONNECT_FACTOR, RECONNECT_MAX_MS);
  }

  function openWs() {
    if (stopped) return;
    try {
      ws = new WebSocket(wsUrl);
    } catch (err) {
      emit(onError, err);
      scheduleReconnect();
      return;
    }

    ws.addEventListener('open', () => {
      reconnectDelay = RECONNECT_BASE_MS;
      emit(onConnect);
      // Fetch HTTP snapshot immediately on connect so UI has full state
      fetchSnapshot();
    });

    ws.addEventListener('message', (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.type === 'hologram.snapshot') {
          emit(onSnapshot, msg.snapshot ?? msg);
        } else if (msg.type === 'hologram.diff') {
          emit(onDiff, msg.diff ?? msg);
        } else if (msg.snapshot) {
          emit(onSnapshot, msg.snapshot);
        } else if (msg.diff) {
          emit(onDiff, msg.diff);
        } else {
          // Treat unknown payloads as diffs
          emit(onDiff, msg);
        }
      } catch (err) {
        emit(onError, err);
      }
    });

    ws.addEventListener('error', (event) => {
      emit(onError, new Error('WebSocket error'));
    });

    ws.addEventListener('close', () => {
      emit(onDisconnect);
      scheduleReconnect();
    });
  }

  return {
    connect() {
      stopped = false;
      openWs();
    },

    disconnect() {
      stopped = true;
      clearTimeout(reconnectTimer);
      if (ws) {
        ws.close();
        ws = null;
      }
    },

    /** Manually trigger a snapshot fetch (e.g. on visibility change). */
    refresh: fetchSnapshot,
  };
}
