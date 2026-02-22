// HeartbeatPulse.tsx — Pulsing dot that beats when runner is active, flatlines on quarantine
import { motion } from 'framer-motion';
import type { SwarmzAnimState } from './useSwarmzAnimState';

export default function HeartbeatPulse({ anim }: { anim: SwarmzAnimState }) {
  const alive = anim.runnerActive && !anim.quarantine;
  const color = anim.quarantine ? '#ff3333' : alive ? '#00ffc8' : '#666';

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
      <motion.div
        animate={
          alive
            ? {
                scale: [1, 1.5, 1],
                opacity: [1, 0.6, 1],
                boxShadow: [
                  `0 0 4px ${color}`,
                  `0 0 16px ${color}`,
                  `0 0 4px ${color}`,
                ],
              }
            : { scale: 1, opacity: 0.4 }
        }
        transition={alive ? { duration: 1.2, repeat: Infinity, ease: 'easeInOut' } : {}}
        style={{
          width: 10,
          height: 10,
          borderRadius: '50%',
          background: color,
          flexShrink: 0,
        }}
      />
      <span
        style={{
          fontFamily: 'monospace',
          fontSize: 11,
          color,
          letterSpacing: 1,
          textTransform: 'uppercase',
        }}
      >
        {anim.quarantine ? 'QUARANTINE' : alive ? 'LIVE' : 'OFFLINE'}
      </span>
    </div>
  );
}
