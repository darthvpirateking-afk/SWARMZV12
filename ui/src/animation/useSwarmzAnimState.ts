import { useState, useEffect, useRef } from 'react';
import type { AvatarRealm } from '../avatar/AvatarState';

export interface SwarmzAnimState {
  mode: string;
  realm: AvatarRealm;
  health: number;           // 0–1 derived from successRate
  evolveLevel: number;
  evolveName: string;
  swarmTier: number;         // 1, 2, or 3
  runnerActive: boolean;
  quarantine: boolean;
  successRate: number;
  pending: number;
  isProcessing: boolean;
}

const modeToRealm = (m: string): AvatarRealm => {
  const up = (m || '').toUpperCase();
  if (up === 'COMPANION') return 'cosmos';
  if (up === 'BUILD') return 'forge';
  if (up === 'HOLOGRAM') return 'void';
  return 'core';
};

const tierFromLevel = (lvl: number): number => {
  if (lvl >= 6) return 3;
  if (lvl >= 3) return 2;
  return 1;
};

const POLL_MS = 12_000;

export function useSwarmzAnimState(): SwarmzAnimState {
  const [state, setState] = useState<SwarmzAnimState>({
    mode: 'COMPANION',
    realm: 'cosmos',
    health: 1,
    evolveLevel: 0,
    evolveName: '',
    swarmTier: 1,
    runnerActive: false,
    quarantine: false,
    successRate: 100,
    pending: 0,
    isProcessing: false,
  });
  const mounted = useRef(true);

  useEffect(() => {
    mounted.current = true;
    const refresh = async () => {
      try {
        const [sysRes, evoRes, modeRes] = await Promise.all([
          fetch('/system/status').then(r => r.ok ? r.json() : null).catch(() => null),
          fetch('/evolve').then(r => r.ok ? r.json() : null).catch(() => null),
          fetch('/v1/mode').then(r => r.ok ? r.json() : null).catch(() => null),
        ]);
        if (!mounted.current) return;

        const modeStr: string = modeRes?.mode || modeRes?.current_mode || 'COMPANION';
        const runner: boolean = !!(sysRes?.runner_active ?? sysRes?.running ?? false);
        const quar: boolean = !!(sysRes?.quarantine ?? false);
        const rate: number = typeof sysRes?.success_rate === 'number' ? sysRes.success_rate : 100;
        const pend: number = typeof sysRes?.pending === 'number' ? sysRes.pending : 0;
        const lvl: number = typeof evoRes?.level === 'number' ? evoRes.level : 0;
        const name: string = evoRes?.name || evoRes?.current_name || '';

        setState({
          mode: modeStr,
          realm: modeToRealm(modeStr),
          health: Math.max(0, Math.min(1, rate / 100)),
          evolveLevel: lvl,
          evolveName: name,
          swarmTier: tierFromLevel(lvl),
          runnerActive: runner,
          quarantine: quar,
          successRate: rate,
          pending: pend,
          isProcessing: runner && pend > 0,
        });
      } catch { /* silent */ }
    };

    refresh();
    const iv = setInterval(refresh, POLL_MS);
    return () => { mounted.current = false; clearInterval(iv); };
  }, []);

  return state;
}
