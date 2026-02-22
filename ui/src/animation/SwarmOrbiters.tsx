// SwarmOrbiters.tsx — Orbiting dots representing active swarm workers
import { motion } from 'framer-motion';
import type { SwarmzAnimState } from './useSwarmzAnimState';

function Orbiter({ index, total, tier }: { index: number; total: number; tier: number }) {
  const angle = (index / total) * 360;
  const radius = 30 + tier * 8;
  const size = 4 + tier;
  const duration = 6 + index * 0.8;
  const hue = 180 + index * 25;

  return (
    <motion.div
      animate={{ rotate: 360 }}
      transition={{ duration, repeat: Infinity, ease: 'linear' }}
      style={{
        position: 'absolute',
        top: '50%',
        left: '50%',
        width: 0,
        height: 0,
      }}
    >
      <motion.div
        style={{
          position: 'absolute',
          width: size,
          height: size,
          borderRadius: '50%',
          background: `hsl(${hue}, 90%, 65%)`,
          boxShadow: `0 0 8px hsl(${hue}, 90%, 65%)`,
          top: -radius,
          left: -size / 2,
        }}
      />
    </motion.div>
  );
}

export default function SwarmOrbiters({ anim }: { anim: SwarmzAnimState }) {
  const tier = anim.swarmTier || 1;
  const count = Math.min(tier * 3, 9);

  return (
    <div
      style={{
        position: 'relative',
        width: 80,
        height: 80,
        flexShrink: 0,
      }}
    >
      {Array.from({ length: count }).map((_, i) => (
        <Orbiter key={i} index={i} total={count} tier={tier} />
      ))}
      {/* Center dot */}
      <motion.div
        animate={{ opacity: [0.5, 1, 0.5] }}
        transition={{ duration: 2, repeat: Infinity }}
        style={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          width: 6,
          height: 6,
          borderRadius: '50%',
          background: '#00ffc8',
          transform: 'translate(-50%, -50%)',
          boxShadow: '0 0 12px rgba(0,255,200,0.5)',
        }}
      />
    </div>
  );
}
