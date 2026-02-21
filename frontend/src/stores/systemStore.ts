import { create } from "zustand";

interface SystemState {
  status: "running" | "stopped" | "restarting" | "degraded" | "unknown";
  uptime: number;
  startTime: string | null;
  offlineMode: boolean;
  lastHeartbeat: string | null;
  activeAgents: number;
  queuedTasks: number;
  systemLoad: number;

  // Actions
  setStatus: (status: SystemState["status"]) => void;
  setUptime: (uptime: number) => void;
  setOfflineMode: (offline: boolean) => void;
  updateFromHealth: (data: {
    ok: boolean;
    uptime_seconds?: number;
    offline_mode?: boolean;
  }) => void;
  updateFromRuntime: (data: {
    active_agents?: number;
    queued_tasks?: number;
    system_load_estimate?: number;
  }) => void;
  setHeartbeat: (ts: string) => void;
}

export const useSystemStore = create<SystemState>((set) => ({
  status: "unknown",
  uptime: 0,
  startTime: null,
  offlineMode: false,
  lastHeartbeat: null,
  activeAgents: 0,
  queuedTasks: 0,
  systemLoad: 0,

  setStatus: (status) => set({ status }),
  setUptime: (uptime) => set({ uptime }),
  setOfflineMode: (offlineMode) => set({ offlineMode }),

  updateFromHealth: (data) =>
    set({
      status: data.ok ? "running" : "degraded",
      uptime: data.uptime_seconds ?? 0,
      offlineMode: data.offline_mode ?? false,
      lastHeartbeat: new Date().toISOString(),
    }),

  updateFromRuntime: (data) =>
    set({
      activeAgents: data.active_agents ?? 0,
      queuedTasks: data.queued_tasks ?? 0,
      systemLoad: data.system_load_estimate ?? 0,
    }),

  setHeartbeat: (ts) => set({ lastHeartbeat: ts }),
}));
