// EvolutionFormWrapper.tsx — Wraps children and applies scale/glow pulse on evolution changes
import { motion, useAnimation } from 'framer-motion';
import { useEffect, useRef, type ReactNode } from 'react';
import type { SwarmzAnimState } from './useSwarmzAnimState';

export default function EvolutionFormWrapper({
  anim,
  children,
}: {
  anim: SwarmzAnimState;
  children: ReactNode;
}) {
  const controls = useAnimation();
  const prevLevel = useRef(anim.evolveLevel);

  useEffect(() => {
    if (anim.evolveLevel !== prevLevel.current) {
      prevLevel.current = anim.evolveLevel;
      controls.start({
        scale: [1, 1.08, 1],
        filter: [
          'brightness(1) drop-shadow(0 0 0px transparent)',
          'brightness(1.4) drop-shadow(0 0 30px rgba(0,255,255,0.6))',
          'brightness(1) drop-shadow(0 0 0px transparent)',
        ],
        transition: { duration: 1.2, ease: 'easeInOut' },
      });
    }
  }, [anim.evolveLevel, controls]);

  return (
    <motion.div animate={controls} style={{ width: '100%', height: '100%' }}>
      {children}
    </motion.div>
  );
}
