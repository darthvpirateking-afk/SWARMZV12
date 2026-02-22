// SystemDistortion.tsx — CSS filter jitter when quarantine is active or health is critically low
import { motion } from 'framer-motion';
import type { SwarmzAnimState } from './useSwarmzAnimState';
import type { ReactNode } from 'react';

export default function SystemDistortion({
  anim,
  children,
}: {
  anim: SwarmzAnimState;
  children: ReactNode;
}) {
  const critical = anim.quarantine || anim.health < 0.2;
  const warning = !critical && anim.health < 0.4;

  const filterAnim = critical
    ? {
        filter: [
          'hue-rotate(0deg) saturate(1) brightness(1)',
          'hue-rotate(5deg) saturate(1.5) brightness(0.95)',
          'hue-rotate(-3deg) saturate(1.2) brightness(1.02)',
          'hue-rotate(0deg) saturate(1) brightness(1)',
        ],
      }
    : warning
      ? {
          filter: [
            'hue-rotate(0deg) brightness(1)',
            'hue-rotate(2deg) brightness(0.98)',
            'hue-rotate(0deg) brightness(1)',
          ],
        }
      : { filter: 'none' };

  const transition = critical
    ? { duration: 0.4, repeat: Infinity, ease: 'easeInOut' as const }
    : warning
      ? { duration: 2, repeat: Infinity, ease: 'easeInOut' as const }
      : { duration: 0.3 };

  return (
    <motion.div
      animate={filterAnim}
      transition={transition}
      style={{ width: '100%', height: '100%' }}
    >
      {children}
    </motion.div>
  );
}
