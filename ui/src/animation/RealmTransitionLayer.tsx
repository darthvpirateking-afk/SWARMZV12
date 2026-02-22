// RealmTransitionLayer.tsx — Full-viewport overlay that fades between realm color palettes
// Realms: GENESIS (cyan), COMBAT (red), VOID (purple), ASCEND (gold)
import { motion, AnimatePresence } from 'framer-motion';
import type { SwarmzAnimState } from './useSwarmzAnimState';

const REALM_COLORS: Record<string, { bg: string; glow: string }> = {
  GENESIS: { bg: 'rgba(0,255,255,0.04)', glow: '0 0 120px rgba(0,255,255,0.15)' },
  COMBAT:  { bg: 'rgba(255,40,40,0.04)',  glow: '0 0 120px rgba(255,40,40,0.15)' },
  VOID:    { bg: 'rgba(140,60,255,0.04)', glow: '0 0 120px rgba(140,60,255,0.15)' },
  ASCEND:  { bg: 'rgba(255,215,0,0.04)',  glow: '0 0 120px rgba(255,215,0,0.15)' },
};

export default function RealmTransitionLayer({ anim }: { anim: SwarmzAnimState }) {
  const realm = anim.realm || 'GENESIS';
  const colors = REALM_COLORS[realm] ?? REALM_COLORS.GENESIS;

  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={realm}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        transition={{ duration: 1.8, ease: 'easeInOut' }}
        style={{
          position: 'fixed',
          inset: 0,
          pointerEvents: 'none',
          zIndex: 0,
          background: colors.bg,
          boxShadow: colors.glow,
        }}
      />
    </AnimatePresence>
  );
}
