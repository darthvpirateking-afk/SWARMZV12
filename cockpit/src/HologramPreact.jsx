import { h } from 'preact';
import { useState, useEffect, useRef } from 'preact/hooks';
import createHologramClient from './hologram-client.esm.js';
import { getCanonicalCockpitBridge } from './canonical_bridge.js';

const STATUS_COLOR = {
  connected: '#00c853',
  connecting: '#ffc107',
  disconnected: '#f44336',
  error: '#f44336',
};

function NodeRow({ node }) {
  const health = typeof node.health === 'number' ? node.health : null;
  const healthClass =
    health !== null
      ? health >= 0.7
        ? 'health-good'
        : health >= 0.4
          ? 'health-warn'
          : 'health-bad'
      : 'health-unknown';

  return h(
    'div',
    { class: 'row' },
    h('span', { class: 'row-id' }, node.id || '--'),
    h('span', { class: 'row-type' }, node.type || 'agent'),
    h('span', { class: `row-health ${healthClass}` }, health !== null ? `${(health * 100).toFixed(0)}%` : '--'),
  );
}

function MissionRow({ mission }) {
  return h(
    'div',
    { class: 'row' },
    h('span', { class: 'row-id' }, mission.id || '--'),
    h('span', { class: 'row-type' }, mission.type || '--'),
    h('span', { class: 'row-status' }, mission.status || '--'),
  );
}

export default function HologramPreact() {
  const [nodes, setNodes] = useState({});
  const [missions, setMissions] = useState({});
  const [wsStatus, setWsStatus] = useState('connecting');
  const [lastTick, setLastTick] = useState(null);
  const [error, setError] = useState(null);
  const clientRef = useRef(null);

  useEffect(() => {
    const bridge = getCanonicalCockpitBridge();
    const client = createHologramClient({
      snapshotUrl: bridge.cockpit.hologramSnapshot,
      wsUrl: bridge.cockpit.hologramWs,

      onSnapshot(snap) {
        setWsStatus('connected');
        setNodes(snap.nodes || {});
        setMissions(snap.missions || {});
        setLastTick(snap.meta?.tick ?? null);
      },

      onDiff(diff) {
        setWsStatus('connected');
        if (diff.nodes && diff.nodes.length) {
          setNodes((prev) => {
            const next = { ...prev };
            for (const n of diff.nodes) {
              next[n.id] = { ...(next[n.id] || {}), ...n };
            }
            return next;
          });
        }
        if (diff.missions && diff.missions.length) {
          setMissions((prev) => {
            const next = { ...prev };
            for (const m of diff.missions) {
              next[m.id] = { ...(next[m.id] || {}), ...m };
            }
            return next;
          });
        }
        if (diff.tick != null) {
          setLastTick(diff.tick);
        }
      },

      onConnect() {
        setWsStatus('connected');
        setError(null);
      },

      onDisconnect() {
        setWsStatus('disconnected');
      },

      onError(err) {
        setWsStatus('error');
        setError(err && err.message ? err.message : String(err));
      },
    });

    clientRef.current = client;
    client.connect();

    return () => {
      client.disconnect();
    };
  }, []);

  const nodeList = Object.values(nodes);
  const missionList = Object.values(missions);
  const healthyAgents = nodeList.filter((n) => typeof n.health === 'number' && n.health >= 0.7).length;
  const activeMissions = missionList.filter((m) => {
    const status = String(m.status || '').toLowerCase();
    return status === 'active' || status === 'running' || status === 'in_progress';
  }).length;

  return h(
    'div',
    { class: 'holo-shell' },
    h(
      'div',
      { class: 'holo-chrome' },
      h(
        'div',
        { class: 'holo-title-wrap' },
        h('div', { class: 'holo-title' }, 'NEXUSMON Hologram Cockpit'),
        h('div', { class: 'holo-subtitle' }, 'Live telemetry stream'),
      ),
      h(
        'div',
        { class: 'status-pill' },
        h('span', {
          class: 'status-dot',
          style: { backgroundColor: STATUS_COLOR[wsStatus] || '#9aa0a6' },
        }),
        h('span', null, `${wsStatus}${lastTick != null ? ` | tick ${lastTick}` : ''}`),
      ),
    ),
    h(
      'div',
      { class: 'metrics-grid' },
      h('div', { class: 'metric-card' }, h('div', { class: 'metric-label' }, 'Agents'), h('div', { class: 'metric-value' }, String(nodeList.length))),
      h('div', { class: 'metric-card' }, h('div', { class: 'metric-label' }, 'Healthy'), h('div', { class: 'metric-value' }, String(healthyAgents))),
      h('div', { class: 'metric-card' }, h('div', { class: 'metric-label' }, 'Missions'), h('div', { class: 'metric-value' }, String(missionList.length))),
      h('div', { class: 'metric-card' }, h('div', { class: 'metric-label' }, 'Active'), h('div', { class: 'metric-value' }, String(activeMissions))),
    ),
    error && h('div', { class: 'error-banner' }, error),
    h(
      'div',
      { class: 'holo-grid' },
      h(
        'section',
        { class: 'panel' },
        h('div', { class: 'panel-head' }, `Agents (${nodeList.length})`),
        nodeList.length === 0 ? h('div', { class: 'empty-state' }, 'Waiting for data...') : nodeList.map((n) => h(NodeRow, { key: n.id, node: n })),
      ),
      h(
        'section',
        { class: 'panel' },
        h('div', { class: 'panel-head' }, `Missions (${missionList.length})`),
        missionList.length === 0 ? h('div', { class: 'empty-state' }, 'Waiting for data...') : missionList.map((m) => h(MissionRow, { key: m.id, mission: m })),
      ),
    ),
  );
}
