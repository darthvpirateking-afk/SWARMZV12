// StatusRing.tsx — SVG ring that fills based on health/success-rate, color-coded
import { motion } from 'framer-motion';
import type { SwarmzAnimState } from './useSwarmzAnimState';

export default function StatusRing({
  anim,
  size = 64,
}: {
  anim: SwarmzAnimState;
  size?: number;
}) {
  const r = (size - 8) / 2;
  const circumference = 2 * Math.PI * r;
  const fill = anim.health * circumference;
  const color =
    anim.health > 0.7
      ? '#00ffc8'
      : anim.health > 0.4
        ? '#ffaa00'
        : '#ff3333';

  return (
    <svg width={size} height={size} style={{ display: 'block' }}>
      {/* background ring */}
      <circle
        cx={size / 2}
        cy={size / 2}
        r={r}
        fill="none"
        stroke="rgba(255,255,255,0.08)"
        strokeWidth={4}
      />
      {/* animated fill ring */}
      <motion.circle
        cx={size / 2}
        cy={size / 2}
        r={r}
        fill="none"
        stroke={color}
        strokeWidth={4}
        strokeLinecap="round"
        strokeDasharray={circumference}
        animate={{ strokeDashoffset: circumference - fill }}
        transition={{ duration: 1.2, ease: 'easeInOut' }}
        style={{
          transform: 'rotate(-90deg)',
          transformOrigin: '50% 50%',
          filter: `drop-shadow(0 0 6px ${color})`,
        }}
      />
      {/* center text */}
      <text
        x="50%"
        y="50%"
        textAnchor="middle"
        dominantBaseline="central"
        fill={color}
        fontSize={size * 0.22}
        fontFamily="monospace"
        fontWeight="bold"
      >
        {Math.round(anim.health * 100)}%
      </text>
    </svg>
  );
}
