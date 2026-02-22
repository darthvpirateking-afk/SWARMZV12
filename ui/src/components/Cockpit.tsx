import { useEffect, useState } from "react";
import { getHealth, getGovernor } from "../api";
import StatusCard from "./StatusCard";
import AvatarPanel from '../avatar/AvatarPanel';

export default function Cockpit() {
  const [health, setHealth] = useState(null);
  const [governor, setGovernor] = useState(null);
  const [showStatus, setShowStatus] = useState(false);

  useEffect(() => {
    getHealth().then(setHealth).catch(() => {});
    getGovernor().then(setGovernor).catch(() => {});
  }, []);

  return (
    <div style={{ position: 'relative', minHeight: 'calc(100vh - 50px)' }}>
      {/* Avatar panel — hero centre-stage */}
      <div style={{ padding: '12px 16px', maxWidth: 960, margin: '0 auto' }}>
        <AvatarPanel />
      </div>

      {/* Status overlay toggle */}
      <button
        onClick={() => setShowStatus(s => !s)}
        style={{
          position: 'fixed', bottom: 16, right: 16, zIndex: 60,
          padding: '7px 14px', borderRadius: 8,
          border: '1px solid #1a3a4a', background: 'rgba(10,16,24,0.9)',
          color: '#00ffff', cursor: 'pointer', fontSize: 12,
          backdropFilter: 'blur(8px)',
          boxShadow: '0 0 12px rgba(0,255,255,0.1)',
        }}
      >
        {showStatus ? '✕ Hide' : '⚙ System'}
      </button>

      {/* Collapsible status drawer */}
      {showStatus && (
        <div style={{
          position: 'fixed', bottom: 50, right: 16, zIndex: 55,
          display: 'flex', flexDirection: 'column', gap: 10,
          animation: 'slide-up .2s ease-out',
        }}>
          <style>{`
            @keyframes slide-up {
              from { opacity: 0; transform: translateY(12px); }
              to   { opacity: 1; transform: translateY(0); }
            }
          `}</style>
          <StatusCard title="Health" data={health} />
          <StatusCard title="Governor" data={governor} />
          <a
            href="/system-log"
            style={{
              display: 'block', textAlign: 'center',
              padding: '8px 14px', borderRadius: 6,
              background: 'rgba(0,255,255,0.07)', border: '1px solid #0e2a3a',
              color: '#00ffff', textDecoration: 'none', fontSize: 12,
              fontFamily: 'monospace', letterSpacing: '1px', fontWeight: 600,
            }}
          >
            VIEW SYSTEM LOG →
          </a>
        </div>
      )}
    </div>
  );
}
