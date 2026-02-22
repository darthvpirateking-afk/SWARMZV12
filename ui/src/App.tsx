import { useState, useEffect } from "react";
import { AnimatedCockpit as Cockpit } from "./animation";

const NAV_LINKS = [
  { label: "SYSTEM LOG", href: "/system-log" },
  { label: "HOLOGRAM",   href: "/hologram" },
  { label: "CONSOLE",    href: "/console" },
] as const;

const MODE_COLORS: Record<string, string> = {
  COMPANION: '#00d4ff',
  BUILD: '#ffaa00',
  HOLOGRAM: '#b050ff',
};

function NavPill({ label, href }: { label: string; href: string }) {
  return (
    <a
      href={href}
      style={{
        fontSize: 10, color: '#445566', fontFamily: "'Courier New', monospace",
        textDecoration: 'none', padding: '4px 10px', borderRadius: 6,
        border: '1px solid #0e2a3a', background: 'rgba(0,255,255,0.03)',
        letterSpacing: '1.5px', transition: 'color .2s, border-color .2s',
        fontWeight: 600,
      }}
      onMouseEnter={e => { const t = e.currentTarget; t.style.color='#00ffff'; t.style.borderColor='#00d4ff'; t.style.background='rgba(0,212,255,0.08)'; }}
      onMouseLeave={e => { const t = e.currentTarget; t.style.color='#445566'; t.style.borderColor='#0e2a3a'; t.style.background='rgba(0,255,255,0.03)'; }}
    >
      {label}
    </a>
  );
}

export default function App() {
  const [clock, setClock] = useState(new Date().toLocaleTimeString());
  const [mode, setMode] = useState('COMPANION');

  useEffect(() => {
    const id = setInterval(() => setClock(new Date().toLocaleTimeString()), 1000);
    return () => clearInterval(id);
  }, []);

  useEffect(() => {
    fetch('/v1/mode').then(r => r.json()).then(d => { if (d.mode) setMode(d.mode); }).catch(() => {});
    const poll = setInterval(() => {
      fetch('/v1/mode').then(r => r.json()).then(d => { if (d.mode) setMode(d.mode); }).catch(() => {});
    }, 8000);
    return () => clearInterval(poll);
  }, []);

  const modeColor = MODE_COLORS[mode] ?? '#888';

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(170deg, #040608 0%, #0a1018 40%, #060a10 100%)',
      position: 'relative',
      overflow: 'hidden',
    }}>
      {/* Scanline overlay */}
      <div style={{
        position: 'fixed', inset: 0, pointerEvents: 'none', zIndex: 999,
        background: 'repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(0,255,255,0.012) 2px, rgba(0,255,255,0.012) 4px)',
      }} />

      {/* Top bar */}
      <header style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '8px 24px',
        borderBottom: '1px solid #0e1e2a',
        background: 'rgba(4,6,10,0.94)',
        backdropFilter: 'blur(16px)',
        position: 'sticky', top: 0, zIndex: 50,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{
            width: 7, height: 7, borderRadius: '50%',
            background: '#00ff88',
            boxShadow: '0 0 6px #00ff88, 0 0 16px #00ff8844',
            animation: 'pulse-dot 2s ease-in-out infinite',
          }} />
          <span style={{
            fontSize: 13, fontWeight: 700, letterSpacing: '4px',
            color: '#00d4ff', textTransform: 'uppercase' as const,
            fontFamily: "'Courier New', monospace",
          }}>
            SWARMZ
          </span>
          {/* Mode pill */}
          <span style={{
            fontSize: 9, fontWeight: 700, letterSpacing: '1.5px',
            color: modeColor, padding: '2px 8px', borderRadius: 4,
            border: `1px solid ${modeColor}33`,
            background: `${modeColor}11`,
            fontFamily: "'Courier New', monospace",
          }}>
            {mode}
          </span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          {NAV_LINKS.map(l => <NavPill key={l.label} {...l} />)}
          <span style={{
            fontSize: 10, color: '#2a3a4a', fontFamily: "'Courier New', monospace",
            marginLeft: 6, letterSpacing: '1px',
          }}>
            {clock}
          </span>
        </div>
      </header>

      <style>{`
        @keyframes pulse-dot {
          0%, 100% { opacity: 1; transform: scale(1); }
          50% { opacity: 0.5; transform: scale(0.85); }
        }
      `}</style>

      <Cockpit />
    </div>
  );
}
