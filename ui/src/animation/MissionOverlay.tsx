// MissionOverlay.tsx — Overlay pulse/spinner when isProcessing is true
import { motion, AnimatePresence } from 'framer-motion';
import type { SwarmzAnimState } from './useSwarmzAnimState';

export default function MissionOverlay({ anim }: { anim: SwarmzAnimState }) {
  return (
    <AnimatePresence>
      {anim.isProcessing && (
        <motion.div
          key="mission-overlay"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.3 }}
          style={{
            position: 'fixed',
            top: 16,
            right: 16,
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            padding: '8px 16px',
            borderRadius: 8,
            background: 'rgba(0,0,0,0.7)',
            border: '1px solid rgba(0,255,200,0.3)',
            zIndex: 9000,
            pointerEvents: 'none',
          }}
        >
          {/* Spinning ring */}
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 1.2, repeat: Infinity, ease: 'linear' }}
            style={{
              width: 18,
              height: 18,
              borderRadius: '50%',
              border: '2px solid transparent',
              borderTopColor: '#00ffc8',
              borderRightColor: '#00ffc8',
            }}
          />
          <span
            style={{
              fontFamily: 'monospace',
              fontSize: 12,
              color: '#00ffc8',
              letterSpacing: 1,
            }}
          >
            MISSION ACTIVE
          </span>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
