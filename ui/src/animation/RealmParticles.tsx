// RealmParticles.tsx — Floating ambient particles colored per realm  
import { motion } from 'framer-motion';
import { useMemo } from 'react';
import type { SwarmzAnimState } from './useSwarmzAnimState';

const REALM_HUE: Record<string, number> = {
  GENESIS: 180,
  COMBAT: 0,
  VOID: 270,
  ASCEND: 45,
};

function FloatingParticle({ hue, index }: { hue: number; index: number }) {
  const size = 2 + Math.random() * 3;
  const x = Math.random() * 100;
  const delay = Math.random() * 8;
  const duration = 12 + Math.random() * 10;

  return (
    <motion.div
      initial={{ y: '110vh', x: `${x}vw`, opacity: 0 }}
      animate={{ y: '-10vh', opacity: [0, 0.6, 0.6, 0] }}
      transition={{
        duration,
        delay,
        repeat: Infinity,
        ease: 'linear',
      }}
      style={{
        position: 'fixed',
        width: size,
        height: size,
        borderRadius: '50%',
        background: `hsl(${hue + index * 3}, 80%, 65%)`,
        pointerEvents: 'none',
        zIndex: 0,
        filter: `blur(${size > 3 ? 1 : 0}px)`,
      }}
    />
  );
}

export default function RealmParticles({ anim }: { anim: SwarmzAnimState }) {
  const realm = anim.realm || 'GENESIS';
  const hue = REALM_HUE[realm] ?? 180;
  const count = 24;

  const particles = useMemo(
    () =>
      Array.from({ length: count }).map((_, i) => (
        <FloatingParticle key={`${realm}-${i}`} hue={hue} index={i} />
      )),
    [realm, hue, count],
  );

  return <>{particles}</>;
}
