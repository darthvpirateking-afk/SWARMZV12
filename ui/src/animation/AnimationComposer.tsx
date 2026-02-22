// AnimationComposer.tsx — Assembles all 12 animation layers into a composited stack
// Renders ambient layers (background, particles, realm, presence) as fixed overlays,
// wraps children in distortion + evolution form wrappers,
// and renders event layers (burst, flare, overlay) on top.
import type { ReactNode } from 'react';
import type { SwarmzAnimState } from './useSwarmzAnimState';

import CockpitBackgroundAnim from './CockpitBackgroundAnim';
import RealmTransitionLayer from './RealmTransitionLayer';
import RealmParticles from './RealmParticles';
import PresenceResonance from './PresenceResonance';
import SystemDistortion from './SystemDistortion';
import EvolutionFormWrapper from './EvolutionFormWrapper';
import StatusRing from './StatusRing';
import HeartbeatPulse from './HeartbeatPulse';
import SwarmOrbiters from './SwarmOrbiters';
import SwarmBurstAnim from './SwarmBurstAnim';
import EvolutionFlare from './EvolutionFlare';
import MissionOverlay from './MissionOverlay';

export default function AnimationComposer({
  anim,
  children,
}: {
  anim: SwarmzAnimState;
  children: ReactNode;
}) {
  return (
    <>
      {/* ── Ambient fixed layers (z behind content) ───────── */}
      <CockpitBackgroundAnim anim={anim} />
      <RealmTransitionLayer anim={anim} />
      <RealmParticles anim={anim} />
      <PresenceResonance anim={anim} />

      {/* ── Content wrapped in distortion + evolution ─────── */}
      <SystemDistortion anim={anim}>
        <EvolutionFormWrapper anim={anim}>
          <div style={{ position: 'relative', zIndex: 1, width: '100%', height: '100%' }}>
            {children}
          </div>
        </EvolutionFormWrapper>
      </SystemDistortion>

      {/* ── HUD overlays ─────────────────────────────────── */}
      <div
        style={{
          position: 'fixed',
          bottom: 16,
          left: 16,
          display: 'flex',
          alignItems: 'center',
          gap: 12,
          zIndex: 9000,
          pointerEvents: 'none',
        }}
      >
        <StatusRing anim={anim} size={52} />
        <HeartbeatPulse anim={anim} />
        <SwarmOrbiters anim={anim} />
      </div>

      {/* ── Event layers (z on top of everything) ─────────── */}
      <SwarmBurstAnim anim={anim} />
      <EvolutionFlare anim={anim} />
      <MissionOverlay anim={anim} />
    </>
  );
}
