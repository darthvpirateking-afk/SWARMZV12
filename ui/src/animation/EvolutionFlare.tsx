// EvolutionFlare.tsx — Bright flare burst when evolution level changes
import { motion, AnimatePresence } from 'framer-motion';
import { useEffect, useRef, useState } from 'react';
import type { SwarmzAnimState } from './useSwarmzAnimState';

export default function EvolutionFlare({ anim }: { anim: SwarmzAnimState }) {
  const [show, setShow] = useState(false);
  const prevName = useRef(anim.evolveName);

  useEffect(() => {
    if (anim.evolveName !== prevName.current && prevName.current) {
      prevName.current = anim.evolveName;
      setShow(true);
      const t = setTimeout(() => setShow(false), 2000);
      return () => clearTimeout(t);
    }
    prevName.current = anim.evolveName;
  }, [anim.evolveName]);

  return (
    <AnimatePresence>
      {show && (
        <motion.div
          key="evo-flare"
          initial={{ opacity: 0, scale: 0.5 }}
          animate={{ opacity: [0, 1, 1, 0], scale: [0.5, 1.2, 1.5, 2] }}
          exit={{ opacity: 0 }}
          transition={{ duration: 1.8, ease: 'easeOut' }}
          style={{
            position: 'fixed',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            width: 200,
            height: 200,
            borderRadius: '50%',
            background: 'radial-gradient(circle, rgba(0,255,255,0.4) 0%, transparent 70%)',
            pointerEvents: 'none',
            zIndex: 9998,
          }}
        >
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: [0, 1, 1, 0], y: [20, 0, -10, -30] }}
            transition={{ duration: 1.8, ease: 'easeOut' }}
            style={{
              position: 'absolute',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              fontFamily: 'monospace',
              fontSize: 16,
              fontWeight: 'bold',
              color: '#00ffc8',
              textShadow: '0 0 20px rgba(0,255,255,0.8)',
              whiteSpace: 'nowrap',
              textTransform: 'uppercase',
            }}
          >
            ↑ {anim.evolveName}
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
