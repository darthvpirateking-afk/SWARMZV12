import { apiGet, apiPost } from "./client";

// ─── Swarm Runner ─────────────────────────────────────────────────────────────
export interface SwarmRunnerStatus {
  ok: boolean;
  runner: string;
  last_tick: string;
  pending_count: number;
  running_count: number;
  success_count: number;
  failure_count: number;
}

// ─── Swarm Units ──────────────────────────────────────────────────────────────
export interface SwarmUnit {
  id: string;
  name: string;
  unit_type: string;
  level: number;
  xp: number;
  status: "IDLE" | "DEPLOYED" | "RECALLED" | string;
  specialization: string | null;
  missions_completed: number;
  missions_failed: number;
  evolution_tier: number;
  abilities: string;
  personal_lore: string;
  created_at: string;
}

export interface SwarmUnitsResponse {
  units: SwarmUnit[];
  count: number;
}

// ─── Organism ─────────────────────────────────────────────────────────────────
export interface OrganismTrait {
  id: string;
  label: string;
  category: string;
  desc: string;
}

export interface OrganismEvolution {
  stage: string;
  stage_rank: number;
  stage_color: string;
  xp: number;
  level: number;
  total_missions: number;
  success_rate: number;
  active_traits: OrganismTrait[];
  recent_events: { type: string; label?: string; timestamp: string; from?: string; to?: string }[];
  mentality: { mood: string; curiosity: number; hunger: number };
}

export interface OrganismWorker {
  id: string;
  goal: string;
  status: string;
  created_at: string;
}

export interface OrganismStatusResponse {
  ok: boolean;
  evolution: OrganismEvolution;
  workers: { active_count: number; active: OrganismWorker[]; total: number };
  operator: {
    total_interactions: number;
    top_categories: string[];
    trust: { approved: number; rejected: number; preference: number };
  };
  claimlab: { belief_count: number };
}

// ─── Signal Modules ───────────────────────────────────────────────────────────
export interface SignalModule {
  module_id: string;
  title: string;
  description: string;
  capabilities: string[];
  status: string;
  enabled: boolean;
}

export interface SignalStatusResponse {
  ok: boolean;
  status: string;
  total_modules: number;
  enabled_modules: number;
  dials: Record<string, number>;
  updated_at: string;
}

export interface SignalModulesResponse {
  ok: boolean;
  count: number;
  modules: Record<string, SignalModule>;
  dials: Record<string, number>;
}

// ─── Operator Rank ────────────────────────────────────────────────────────────
export interface OperatorRank {
  rank: string;
  xp: number;
  next_rank: string;
  xp_needed: number;
  progress: number;
  traits: string[];
  permissions: Record<string, boolean>;
  missions: {
    active_missions: number;
    completed_today: number;
    total_xp_from_missions: number;
    latest_completed_goal: string | null;
    progress_pct: number;
  };
}

// ─── Cognition ────────────────────────────────────────────────────────────────
export interface CognitionStatus {
  ok: boolean;
  predictions: { total: number; resolved: number; avg_brier: number | null };
  beliefs: { graph_nodes: number; graph_edges: number };
  errors: { total: number; patterns: string[]; dominant: string | null };
  memory: { total: number; avg_distortion: number | null };
  attention: { sessions: number; avg_focus: number | null };
}

// ─── Awareness ────────────────────────────────────────────────────────────────
export interface AwarenessAlerts {
  ok: boolean;
  alerts: {
    variance_rising: boolean;
    coupling_detected: boolean;
    bounded_results: boolean;
    success_rate: number;
    total_missions: number;
  };
}

export interface TopologyNode {
  mission_id: string;
  size: number;
  status: string;
  last_event_at: string;
  resources: string[];
  risk: number;
}

export interface AwarenessTopology {
  ok: boolean;
  topology: {
    nodes: TopologyNode[];
    edges: { source: string; target: string; weight?: number }[];
    meta: { total_events: number; total_missions: number };
  };
}

// ─── Evolution ────────────────────────────────────────────────────────────────
export interface EvolutionStatus {
  ok: boolean;
  total_missions: number;
  success_rate: number;
  current_stage: string;
  level: number;
  xp: number;
  success_count: number;
  active_traits: OrganismTrait[];
}

// ─── API calls ────────────────────────────────────────────────────────────────
export const swarmApi = {
  runnerStatus: () => apiGet<SwarmRunnerStatus>("/v1/swarm/status"),
  units: () => apiGet<SwarmUnitsResponse>("/v1/nexusmon/swarm/units"),
  deployUnit: (id: string) =>
    apiPost<{ ok: boolean }>(`/v1/nexusmon/swarm/units/${id}/deploy`, {}),
  recallUnit: (id: string) =>
    apiPost<{ ok: boolean }>(`/v1/nexusmon/swarm/units/${id}/recall`, {}),
};

export const organismApi = {
  status: () => apiGet<OrganismStatusResponse>("/v1/nexusmon/organism/status"),
  spawnWorker: (goal: string) =>
    apiPost<{ ok: boolean; worker: OrganismWorker }>(
      "/v1/nexusmon/organism/worker/spawn",
      { goal },
    ),
};

export const signalApi = {
  status: () => apiGet<SignalStatusResponse>("/v1/nexusmon/signal/status"),
  modules: () => apiGet<SignalModulesResponse>("/v1/nexusmon/signal/modules"),
  setDial: (dial: string, value: number) =>
    apiPost<{ ok: boolean }>("/v1/nexusmon/signal/dials", { dial, value }),
};

export const operatorApi = {
  rank: () => apiGet<OperatorRank>("/v1/operator/rank"),
};

export const cognitionApi = {
  status: () => apiGet<CognitionStatus>("/v1/cognition/status"),
};

export const awarenessApi = {
  alerts: () => apiGet<AwarenessAlerts>("/v1/awareness/alerts"),
  topology: () => apiGet<AwarenessTopology>("/v1/awareness/topology"),
};

export const evolutionApi = {
  full: () => apiGet<EvolutionStatus>("/v1/evolution/full"),
};
