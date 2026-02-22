// ArtifactOrb.tsx — Floating, clickable artifact orb that appears when missions produce artifacts
// Click → expands to show contents → NEXUSMON absorbs the data
import { motion, AnimatePresence } from 'framer-motion';
import { useState } from 'react';

export type ArtifactData = {
  id: string;
  type: string;
  source: string;
  timestamp: string;
  payload: any;
  links?: string[];
  mission_id?: string;
  worker_id?: string;
  status?: string;
  intent?: string;
  duration_ms?: number;
};

type OrbPhase = 'orbiting' | 'expanded' | 'absorbing' | 'absorbed';

export default function ArtifactOrb({
  artifact,
  accentColor = '#00ffc8',
  onAbsorb,
  onDismiss,
}: {
  artifact: ArtifactData;
  accentColor?: string;
  onAbsorb: (artifact: ArtifactData) => void;
  onDismiss: () => void;
}) {
  const [phase, setPhase] = useState<OrbPhase>('orbiting');

  const typeIcon: Record<string, string> = {
    mission: '🔮', worker: '⚙️', evolution: '🧬', system: '🛡️', operator: '◇',
  };
  const icon = typeIcon[artifact.type] ?? '💎';

  const handleClick = () => {
    if (phase === 'orbiting') setPhase('expanded');
  };

  const handleAbsorb = () => {
    setPhase('absorbing');
    setTimeout(() => {
      setPhase('absorbed');
      onAbsorb(artifact);
    }, 900);
  };

  /* ── orbiting (small floating orb) ─────────────────────── */
  if (phase === 'orbiting') {
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0, y: 30 }}
        animate={{
          opacity: 1,
          scale: [1, 1.1, 1],
          y: [0, -8, 0],
        }}
        transition={{
          opacity: { duration: 0.5 },
          scale: { duration: 2.5, repeat: Infinity, ease: 'easeInOut' },
          y: { duration: 3, repeat: Infinity, ease: 'easeInOut' },
        }}
        onClick={handleClick}
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: 8,
          padding: '8px 16px',
          borderRadius: 20,
          background: 'rgba(0,0,0,0.7)',
          border: `1px solid ${accentColor}55`,
          boxShadow: `0 0 20px ${accentColor}33, inset 0 0 15px ${accentColor}11`,
          cursor: 'pointer',
          fontFamily: "'Courier New', monospace",
          userSelect: 'none',
          position: 'relative',
          zIndex: 100,
        }}
        whileHover={{
          scale: 1.08,
          boxShadow: `0 0 30px ${accentColor}66, inset 0 0 20px ${accentColor}22`,
        }}
      >
        {/* Pulsing glow ring */}
        <motion.div
          animate={{ opacity: [0.3, 0.8, 0.3] }}
          transition={{ duration: 2, repeat: Infinity }}
          style={{
            position: 'absolute',
            inset: -3,
            borderRadius: 22,
            border: `1px solid ${accentColor}44`,
            pointerEvents: 'none',
          }}
        />
        <span style={{ fontSize: 18 }}>{icon}</span>
        <div>
          <div style={{ fontSize: 10, color: accentColor, fontWeight: 700, letterSpacing: 1 }}>
            ARTIFACT PRODUCED
          </div>
          <div style={{ fontSize: 9, color: '#6688aa', letterSpacing: 0.5 }}>
            {artifact.type?.toUpperCase()} │ {artifact.id?.slice(0, 12)}..
          </div>
        </div>
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 8, repeat: Infinity, ease: 'linear' }}
          style={{ fontSize: 11, color: accentColor, opacity: 0.4 }}
        >
          ◈
        </motion.div>
      </motion.div>
    );
  }

  /* ── expanded (full artifact card) ─────────────────────── */
  if (phase === 'expanded') {
    const payloadStr = artifact.payload
      ? JSON.stringify(artifact.payload, null, 2).slice(0, 500)
      : '(no payload)';

    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.8, y: 10 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        transition={{ duration: 0.4, ease: 'easeOut' }}
        style={{
          width: '100%',
          maxWidth: 500,
          margin: '0 auto',
          padding: 0,
          borderRadius: 14,
          border: `1px solid ${accentColor}44`,
          background: 'rgba(2,6,14,0.95)',
          boxShadow: `0 0 40px ${accentColor}22`,
          fontFamily: "'Courier New', monospace",
          overflow: 'hidden',
          position: 'relative',
          zIndex: 100,
        }}
      >
        {/* Header */}
        <div style={{
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          padding: '10px 14px',
          background: `linear-gradient(90deg, ${accentColor}11, transparent)`,
          borderBottom: `1px solid ${accentColor}22`,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ fontSize: 16 }}>{icon}</span>
            <div>
              <div style={{ fontSize: 11, color: accentColor, fontWeight: 700, letterSpacing: 1 }}>
                {artifact.type?.toUpperCase()} ARTIFACT
              </div>
              <div style={{ fontSize: 9, color: '#556677' }}>{artifact.id}</div>
            </div>
          </div>
          <motion.button
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
            onClick={onDismiss}
            style={{
              background: 'none', border: 'none', color: '#556677',
              cursor: 'pointer', fontSize: 14, fontFamily: 'monospace', padding: '2px 6px',
            }}
          >✕</motion.button>
        </div>

        {/* Meta */}
        <div style={{ padding: '10px 14px', fontSize: 10, color: '#6688aa', lineHeight: 1.6 }}>
          {artifact.intent && <div><span style={{ color: '#445566' }}>INTENT:</span> {artifact.intent}</div>}
          {artifact.worker_id && <div><span style={{ color: '#445566' }}>WORKER:</span> {artifact.worker_id}</div>}
          {artifact.status && <div><span style={{ color: '#445566' }}>STATUS:</span> <span style={{ color: artifact.status === 'completed' ? '#00ff88' : '#ff6644' }}>{artifact.status}</span></div>}
          {artifact.duration_ms != null && <div><span style={{ color: '#445566' }}>DURATION:</span> {artifact.duration_ms}ms</div>}
          <div><span style={{ color: '#445566' }}>SOURCE:</span> {artifact.source}</div>
          <div><span style={{ color: '#445566' }}>TIME:</span> {artifact.timestamp}</div>
        </div>

        {/* Payload */}
        <div style={{
          padding: '10px 14px',
          borderTop: `1px solid ${accentColor}11`,
          maxHeight: 180,
          overflowY: 'auto',
          scrollbarWidth: 'thin' as const,
          scrollbarColor: `${accentColor}33 transparent`,
        }}>
          <div style={{ fontSize: 9, color: '#445566', letterSpacing: 1, marginBottom: 6 }}>PAYLOAD</div>
          <pre style={{
            fontSize: 10, color: '#8899aa', margin: 0, whiteSpace: 'pre-wrap',
            wordBreak: 'break-all' as const, lineHeight: 1.4,
          }}>
            {payloadStr}
          </pre>
        </div>

        {/* Absorb button */}
        <div style={{ padding: '10px 14px', borderTop: `1px solid ${accentColor}11` }}>
          <motion.button
            whileHover={{ scale: 1.03, boxShadow: `0 0 20px ${accentColor}44` }}
            whileTap={{ scale: 0.97 }}
            onClick={handleAbsorb}
            style={{
              width: '100%',
              padding: '10px',
              borderRadius: 8,
              border: `1px solid ${accentColor}`,
              background: `linear-gradient(145deg, ${accentColor}22, rgba(0,0,0,0.6))`,
              color: accentColor,
              cursor: 'pointer',
              fontFamily: "'Courier New', monospace",
              fontWeight: 700,
              fontSize: 11,
              letterSpacing: 2,
            }}
          >
            ◈ NEXUSMON ABSORB DATA ◈
          </motion.button>
        </div>
      </motion.div>
    );
  }

  /* ── absorbing animation ───────────────────────────────── */
  if (phase === 'absorbing') {
    return (
      <motion.div
        initial={{ opacity: 1, scale: 1 }}
        animate={{
          opacity: 0,
          scale: 0.2,
          y: -80,
          rotate: 180,
          filter: `brightness(2) drop-shadow(0 0 30px ${accentColor})`,
        }}
        transition={{ duration: 0.8, ease: 'easeIn' }}
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: 20,
          fontFamily: "'Courier New', monospace",
          color: accentColor,
          fontSize: 14,
          fontWeight: 700,
          letterSpacing: 2,
        }}
      >
        <span style={{ fontSize: 24 }}>{icon}</span>
        <span style={{ marginLeft: 10 }}>ABSORBING...</span>
      </motion.div>
    );
  }

  /* ── absorbed (gone) ───────────────────────────────────── */
  return null;
}
