/**
 * Core type definitions for SWARMZ Ultimate Layout
 */

/**
 * Task packet that flows through the system
 */
export interface TaskPacket {
  id: string;
  intent: string;
  action: string;
  parameters: Record<string, any>;
  context: {
    user_id?: string;
    session_id?: string;
    timestamp: number;
  };
  safety_level: "safe" | "needs_confirm" | "blocked";
  priority: number;
}

/**
 * Result returned by workers
 */
export interface WorkerResult {
  task_id: string;
  status: "success" | "failure" | "partial";
  data: any;
  artifacts: string[];
  cost: {
    time_ms: number;
    tokens?: number;
    api_calls?: number;
  };
  errors?: string[];
}

/**
 * Commit state for actions
 */
export type CommitState = "ACTION_READY" | "NEEDS_CONFIRM" | "BLOCKED";

/**
 * Action interface that all actions must implement
 */
export interface Action {
  preview(): Promise<string>;
  execute(): Promise<any>;
  rollback(): Promise<void>;
}

/**
 * Mode for the interface layer
 */
export type InterfaceMode = "companion" | "operator";

/**
 * Metric entry for tracking performance
 */
export interface MetricEntry {
  timestamp: number;
  action: string;
  duration_ms: number;
  cost: number;
  success: boolean;
  error?: string;
  roi_proxy?: number;
}

/**
 * Patch pack for evolution
 */
export interface PatchPack {
  version: string;
  changes: Array<{
    file: string;
    diff: string;
  }>;
  rationale: string;
  metrics_justification: string;
}

/**
 * Artifact pack saved under ./packs/
 */
export interface ArtifactPack {
  id: string;
  task_id: string;
  intent: string;
  artifacts: string[];
  verification: {
    passed: boolean;
    checks: number;
    errors: string[];
  };
  rank: number;
  created_at: number;
  cycle_ms: number;
}
