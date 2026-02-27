import { h } from 'preact';
import { useState, useEffect, useRef } from 'preact/hooks';
import createHologramClient from './hologram-client.esm.js';

const STATUS_COLOR = {
  connected: '#00c853',
  connecting: '#ffc107',
  disconnected: '#f44336',
  error: '#f44336',
};

function NodeRow({ node }) {
  const health = typeof node.health === 'number' ? node.health : null;
  return h('div', { class: 'row' },
    h('span', null, node.id || '—'),
    h('span', null, node.type || 'agent'),
    h('span', {
      style: {
        color: health !== null ? (health >= 0.7 ? '#00c853' : health >= 0.4 ? '#ffc107' : '#f44336') : '#aaa',
      },
    }, health !== null ? `${(health * 100).toFixed(0)}%` : '—'),
  );
}

function MissionRow({ mission }) {
  return h('div', { class: 'row' },
    h('span', null, mission.id || '—'),
    h('span', null, mission.type || '—'),
    h('span', null, mission.status || '—'),
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
    const client = createHologramClient({
      snapshotUrl: '/hologram/snapshot/latest',
      wsUrl: `${location.protocol === 'https:' ? 'wss' : 'ws'}://${location.host}/hologram/ws`,

      onSnapshot(snap) {
        setWsStatus('connected');
        setNodes(snap.nodes || {});
        setMissions(snap.missions || {});
        setLastTick(snap.meta?.tick ?? null);
      },

      onDiff(diff) {
        setWsStatus('connected');
        if (diff.nodes && diff.nodes.length) {
          setNodes(prev => {
            const next = { ...prev };
            for (const n of diff.nodes) {
              // Bug-fixed: use n.id as key, not the object n itself
              next[n.id] = { ...(next[n.id] || {}), ...n };
            }
            return next;
          });
        }
        if (diff.missions && diff.missions.length) {
          setMissions(prev => {
            const next = { ...prev };
            for (const m of diff.missions) {
              // Bug-fixed: use m.id as key, not the object m itself
              next[m.id] = { ...(next[m.id] || {}), ...m };
            }
            return next;
          });
        }
        if (diff.tick != null) setLastTick(diff.tick);
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

  return h('div', { class: 'holo-root' },
    h('div', { class: 'holo-header' },
      'NEXUSMON Hologram ',
      h('span', {
        style: {
          fontSize: 12,
          fontWeight: 400,
          color: STATUS_COLOR[wsStatus] || '#aaa',
          marginLeft: 8,
        },
      }, `● ${wsStatus}${lastTick != null ? ` · tick ${lastTick}` : ''}`),
    ),
    error && h('div', { style: { color: '#f44336', fontSize: 12, marginBottom: 8 } }, error),
    h('div', { class: 'holo-grid' },
      h('div', { class: 'panel' },
        h('div', { style: { fontWeight: 600, marginBottom: 6, fontSize: 13 } },
          `Agents (${nodeList.length})`),
        nodeList.length === 0
          ? h('div', { style: { color: '#aaa', fontSize: 12 } }, 'Waiting for data…')
          : nodeList.map(n => h(NodeRow, { key: n.id, node: n })),
      ),
      h('div', { class: 'panel' },
        h('div', { style: { fontWeight: 600, marginBottom: 6, fontSize: 13 } },
          `Missions (${missionList.length})`),
        missionList.length === 0
          ? h('div', { style: { color: '#aaa', fontSize: 12 } }, 'Waiting for data…')
          : missionList.map(m => h(MissionRow, { key: m.id, mission: m })),
      ),
    ),
  );
}
