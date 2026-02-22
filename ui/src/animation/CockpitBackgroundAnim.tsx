// CockpitBackgroundAnim.tsx — Animated gradient background that shifts with realm + health
import { motion } from 'framer-motion';
import type { SwarmzAnimState } from './useSwarmzAnimState';

const realmGradients: Record<string, string> = {
  GENESIS: 'radial-gradient(ellipse at 50% 50%, rgba(0,40,60,0.9) 0%, rgba(0,10,20,1) 100%)',
  COMBAT:  'radial-gradient(ellipse at 50% 50%, rgba(60,10,10,0.9) 0%, rgba(20,0,0,1) 100%)',
  VOID:    'radial-gradient(ellipse at 50% 50%, rgba(30,10,60,0.9) 0%, rgba(10,0,20,1) 100%)',
  ASCEND:  'radial-gradient(ellipse at 50% 50%, rgba(50,40,10,0.9) 0%, rgba(20,15,0,1) 100%)',
};

export default function CockpitBackgroundAnim({ anim }: { anim: SwarmzAnimState }) {
  const realm = anim.realm || 'GENESIS';
  const gradient = realmGradients[realm] ?? realmGradients.GENESIS;
  // Low health → red tinge overlay
  const healthOverlay = anim.health < 0.3 ? 'rgba(255,0,0,0.08)' : 'transparent';

  return (
    <motion.div
      animate={{ background: gradient }}
      transition={{ duration: 2.5, ease: 'easeInOut' }}
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: -1,
        pointerEvents: 'none',
      }}
    >
      <motion.div
        animate={{ background: healthOverlay }}
        transition={{ duration: 1 }}
        style={{ width: '100%', height: '100%' }}
      />
    </motion.div>
  );
}
