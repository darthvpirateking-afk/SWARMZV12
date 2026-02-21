import { create } from "zustand";

interface AutonomyState {
  level: number;
  mode: string;
  requested_level?: number;
  updated_at?: string;
}

interface PartnerState {
  name: string;
  tier: string;
  tier_index: number;
  traits: Record<string, number>;
  autonomy_ceiling: number;
}

interface ShadowState {
  name: string;
  tier: string;
  tier_index: number;
  risk_precision: number;
  tactical_authority: string;
}

interface ShadowModeState {
  enabled: boolean;
  lane: string;
  last_activation: string | null;
}

interface CockpitState {
  autonomy: AutonomyState;
  partner: PartnerState;
  shadow: ShadowState;
  shadowMode: ShadowModeState;
  mode: "COMPANION" | "BUILD";
  phase: string;
  loading: boolean;

  // Actions
  setAutonomy: (autonomy: AutonomyState) => void;
  setPartner: (partner: PartnerState) => void;
  setShadow: (shadow: ShadowState) => void;
  setShadowMode: (shadowMode: ShadowModeState) => void;
  setMode: (mode: "COMPANION" | "BUILD") => void;
  setPhase: (phase: string) => void;
  setLoading: (loading: boolean) => void;
  updateFromCommandCenter: (data: Record<string, unknown>) => void;
}

export const useCockpitStore = create<CockpitState>((set) => ({
  autonomy: { level: 35, mode: "assisted" },
  partner: {
    name: "AegisShade",
    tier: "Rookie",
    tier_index: 1,
    traits: { logic: 0.6, empathy: 0.64, precision: 0.62 },
    autonomy_ceiling: 25,
  },
  shadow: {
    name: "NightLegion",
    tier: "Dormant",
    tier_index: 0,
    risk_precision: 0.35,
    tactical_authority: "operator_approval",
  },
  shadowMode: { enabled: false, lane: "mirror", last_activation: null },
  mode: "COMPANION",
  phase: "AWAKENING",
  loading: false,

  setAutonomy: (autonomy) => set({ autonomy }),
  setPartner: (partner) => set({ partner }),
  setShadow: (shadow) => set({ shadow }),
  setShadowMode: (shadowMode) => set({ shadowMode }),
  setMode: (mode) => set({ mode }),
  setPhase: (phase) => set({ phase }),
  setLoading: (loading) => set({ loading }),

  updateFromCommandCenter: (data) =>
    set((s) => ({
      autonomy: (data.autonomy as AutonomyState) ?? s.autonomy,
      partner: (data.partner as PartnerState) ?? s.partner,
      shadow: (data.shadow as ShadowState) ?? s.shadow,
      shadowMode: (data.shadow_mode as ShadowModeState) ?? s.shadowMode,
    })),
}));
