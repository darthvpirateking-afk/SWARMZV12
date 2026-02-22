// SwarmBurstAnim.tsx — Particle burst when tier upgrades or big events fire
import { motion, AnimatePresence } from 'framer-motion';
import { useEffect, useRef, useState } from 'react';
import type { SwarmzAnimState } from './useSwarmzAnimState';

function Particle({ i, total }: { i: number; total: number }) {
  const angle = (i / total) * Math.PI * 2;
  const dist = 80 + Math.random() * 60;
  return (
    <motion.div
      initial={{ x: 0, y: 0, opacity: 1, scale: 1 }}
      animate={{
        x: Math.cos(angle) * dist,
        y: Math.sin(angle) * dist,
        opacity: 0,
        scale: 0.2,
      }}
      transition={{ duration: 0.9 + Math.random() * 0.4, ease: 'easeOut' }}
      style={{
        position: 'absolute',
        width: 6,
        height: 6,
        borderRadius: '50%',
        background: `hsl(${180 + i * 15}, 100%, 70%)`,
        pointerEvents: 'none',
      }}
    />
  );
}

export default function SwarmBurstAnim({ anim }: { anim: SwarmzAnimState }) {
  const [burst, setBurst] = useState(false);
  const prevTier = useRef(anim.swarmTier);
  const COUNT = 18;

  useEffect(() => {
    if (anim.swarmTier > prevTier.current) {
      prevTier.current = anim.swarmTier;
      setBurst(true);
      const t = setTimeout(() => setBurst(false), 1500);
      return () => clearTimeout(t);
    }
    prevTier.current = anim.swarmTier;
  }, [anim.swarmTier]);

  return (
    <AnimatePresence>
      {burst && (
        <motion.div
          key="burst"
          initial={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          style={{
            position: 'fixed',
            top: '50%',
            left: '50%',
            pointerEvents: 'none',
            zIndex: 9999,
          }}
        >
          {Array.from({ length: COUNT }).map((_, i) => (
            <Particle key={i} i={i} total={COUNT} />
          ))}
        </motion.div>
      )}
    </AnimatePresence>
  );
}
