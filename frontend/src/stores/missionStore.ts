import { create } from "zustand";

interface Mission {
  mission_id: string;
  goal: string;
  category: string;
  status: string;
  constraints: Record<string, unknown>;
  results: Record<string, unknown>;
  created_at: string;
  updated_at?: string;
  started_at?: string;
  intent?: string;
}

interface MissionState {
  missions: Mission[];
  loading: boolean;
  error: string | null;
  selectedMissionId: string | null;

  // Actions
  setMissions: (missions: Mission[]) => void;
  addMission: (mission: Mission) => void;
  updateMission: (id: string, updates: Partial<Mission>) => void;
  removeMission: (id: string) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  selectMission: (id: string | null) => void;

  // Computed
  pendingCount: () => number;
  runningCount: () => number;
  completedCount: () => number;
}

export const useMissionStore = create<MissionState>((set, get) => ({
  missions: [],
  loading: false,
  error: null,
  selectedMissionId: null,

  setMissions: (missions) => set({ missions, loading: false, error: null }),
  addMission: (mission) =>
    set((s) => ({ missions: [mission, ...s.missions] })),
  updateMission: (id, updates) =>
    set((s) => ({
      missions: s.missions.map((m) =>
        m.mission_id === id ? { ...m, ...updates } : m,
      ),
    })),
  removeMission: (id) =>
    set((s) => ({
      missions: s.missions.filter((m) => m.mission_id !== id),
    })),
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error, loading: false }),
  selectMission: (id) => set({ selectedMissionId: id }),

  pendingCount: () =>
    get().missions.filter((m) =>
      ["PENDING", "QUEUED", "CREATED"].includes(m.status.toUpperCase()),
    ).length,
  runningCount: () =>
    get().missions.filter((m) => m.status.toUpperCase() === "RUNNING").length,
  completedCount: () =>
    get().missions.filter((m) =>
      ["SUCCESS", "COMPLETED", "DONE"].includes(m.status.toUpperCase()),
    ).length,
}));
