// PresenceResonance.tsx — Subtle breathing glow around the main cockpit area
import { motion } from 'framer-motion';
import type { SwarmzAnimState } from './useSwarmzAnimState';

export default function PresenceResonance({ anim }: { anim: SwarmzAnimState }) {
  const alive = anim.runnerActive && !anim.quarantine;
  const color = anim.quarantine
    ? 'rgba(255,50,50,0.08)'
    : alive
      ? 'rgba(0,255,200,0.06)'
      : 'rgba(100,100,100,0.04)';

  return (
    <motion.div
      animate={
        alive
          ? {
              boxShadow: [
                `inset 0 0 60px ${color}`,
                `inset 0 0 120px ${color}`,
                `inset 0 0 60px ${color}`,
              ],
            }
          : { boxShadow: `inset 0 0 40px ${color}` }
      }
      transition={alive ? { duration: 4, repeat: Infinity, ease: 'easeInOut' } : {}}
      style={{
        position: 'fixed',
        inset: 0,
        pointerEvents: 'none',
        zIndex: 0,
        borderRadius: 0,
      }}
    />
  );
}
