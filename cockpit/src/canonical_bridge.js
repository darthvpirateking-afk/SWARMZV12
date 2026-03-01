const CANONICAL_API_BASE = '/v1/canonical';
const CANONICAL_HOLOGRAM_BASE = '/v1/canonical/cockpit/hologram';

function toWsUrl(path) {
  if (typeof location === 'undefined') {
    return `ws://localhost${path}`;
  }
  const scheme = location.protocol === 'https:' ? 'wss' : 'ws';
  return `${scheme}://${location.host}${path}`;
}

const CANONICAL_BRIDGE = Object.freeze({
  apiBase: CANONICAL_API_BASE,
  cockpit: Object.freeze({
    state: `${CANONICAL_API_BASE}/cockpit/state`,
    hologramSnapshot: `${CANONICAL_HOLOGRAM_BASE}/snapshot/latest`,
    hologramPatch: `${CANONICAL_HOLOGRAM_BASE}/patch`,
    hologramWs: toWsUrl(`${CANONICAL_HOLOGRAM_BASE}/ws`),
  }),
});

if (typeof window !== 'undefined') {
  window.__NEXUSMON_CANONICAL_BRIDGE__ = CANONICAL_BRIDGE;
}

export function getCanonicalCockpitBridge() {
  if (typeof window !== 'undefined' && window.__NEXUSMON_CANONICAL_BRIDGE__) {
    return window.__NEXUSMON_CANONICAL_BRIDGE__;
  }
  return CANONICAL_BRIDGE;
}

export default CANONICAL_BRIDGE;
