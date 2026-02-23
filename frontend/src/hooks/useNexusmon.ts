import { useCallback, useEffect, useMemo, useState } from "react";
import { apiGet } from "../api/client";

export interface NexusmonTraits {
  curiosity: number;
  loyalty: number;
  aggression: number;
  creativity: number;
  autonomy: number;
  patience: number;
  protectiveness: number;
}

export interface NexusmonEntity {
  name?: string;
  form?: string;
  mood?: string;
  xp?: number;
  xp_pct?: number;
  traits: NexusmonTraits;
}

interface NexusmonState {
  entity: NexusmonEntity | null;
  loading: boolean;
  error: string | null;
}

const DEFAULT_TRAITS: NexusmonTraits = {
  curiosity: 0,
  loyalty: 0,
  aggression: 0,
  creativity: 0,
  autonomy: 0,
  patience: 0,
  protectiveness: 0,
};

const initialState: NexusmonState = {
  entity: null,
  loading: false,
  error: null,
};

function normalizeTraits(input: Record<string, unknown> | undefined): NexusmonTraits {
  const raw = input ?? {};

  const toPercent = (value: unknown): number => {
    const n = Number(value ?? 0);
    if (Number.isNaN(n)) {
      return 0;
    }
    if (n <= 1) {
      return Math.round(Math.max(0, Math.min(1, n)) * 100);
    }
    return Math.round(Math.max(0, Math.min(100, n)));
  };

  return {
    curiosity: toPercent(raw.curiosity),
    loyalty: toPercent(raw.loyalty),
    aggression: toPercent(raw.aggression),
    creativity: toPercent(raw.creativity),
    autonomy: toPercent(raw.autonomy),
    patience: toPercent(raw.patience),
    protectiveness: toPercent(raw.protectiveness),
  };
}

export function useNexusmon() {
  const [state, setState] = useState<NexusmonState>(initialState);

  const refresh = useCallback(async () => {
    setState((prev) => ({ ...prev, loading: true, error: null }));
    try {
      let payload: Record<string, unknown>;
      try {
        payload = await apiGet<Record<string, unknown>>("/v1/nexusmon/entity");
      } catch {
        payload = await apiGet<Record<string, unknown>>("/v1/nexusmon/entity/state");
      }

      const entityShape = (payload.entity as Record<string, unknown> | undefined) ?? payload;
      const traits = normalizeTraits(entityShape.traits as Record<string, unknown> | undefined);

      const entity: NexusmonEntity = {
        name: String(entityShape.name ?? "NEXUSMON"),
        form: String(entityShape.form ?? "ROOKIE"),
        mood: String(entityShape.mood ?? "calm"),
        xp: Number(entityShape.xp ?? 0),
        xp_pct: Number(entityShape.xp_pct ?? 0),
        traits,
      };

      setState({ entity, loading: false, error: null });
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Failed to load NEXUSMON entity";
      setState((prev) => ({ ...prev, loading: false, error: message }));
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const traits = state.entity?.traits ?? DEFAULT_TRAITS;

  const gates = useMemo(
    () => ({
      canAggressiveScan: traits.aggression >= 66,
      delegationEnabled: traits.autonomy >= 45,
      dryRunRequired: traits.protectiveness >= 70,
      parallelMissionsAllowed: traits.autonomy >= 60,
      firecrawlEnabled: traits.curiosity >= 55,
      graphRagEnabled: traits.curiosity >= 70,
      deepFingerprintEnabled: traits.curiosity >= 60,
      skillInstallEnabled: traits.creativity >= 70,
      dcgActive: true,
      rollbackAvailable: traits.protectiveness >= 50,
      lintBlocksOnWarnings: traits.protectiveness >= 70,
      kanbanEnabled: traits.patience >= 30,
      traitProposalsVisible: traits.patience >= 40,
      contextInjecting: traits.curiosity >= 40,
    }),
    [traits],
  );

  return {
    ...state,
    traits,
    gates,
    refresh,
  };
}
