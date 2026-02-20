export type PartnerForm = "Seed" | "Scout" | "Operator" | "Architect";

export type ArmyRole = "Tank" | "DPS" | "Support" | "Specialist";

export interface ArmyUnit {
  id: string;
  role: ArmyRole;
  rarity: "Common" | "Rare" | "Epic" | "Legendary";
  level: number;
}

export interface PlayerProgress {
  playerLevel: number;
  partnerLevel: number;
  partnerForm: PartnerForm;
  partnerXp: number;
  army: ArmyUnit[];
  chipLevel: number;
  buildingLevel: number;
  gateTier: number;
  dataShards: number;
}

const STORAGE_KEY = "gate_link_progress_v1";

export const DEFAULT_PROGRESS: PlayerProgress = {
  playerLevel: 1,
  partnerLevel: 1,
  partnerForm: "Seed",
  partnerXp: 0,
  army: [
    { id: "shadow-1", role: "DPS", rarity: "Common", level: 1 },
  ],
  chipLevel: 1,
  buildingLevel: 1,
  gateTier: 1,
  dataShards: 0,
};

export function loadProgress(): PlayerProgress {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return structuredClone(DEFAULT_PROGRESS);
    const parsed = JSON.parse(raw) as Partial<PlayerProgress>;
    return {
      ...structuredClone(DEFAULT_PROGRESS),
      ...parsed,
      army: Array.isArray(parsed.army) && parsed.army.length > 0 ? parsed.army : structuredClone(DEFAULT_PROGRESS.army),
    };
  } catch {
    return structuredClone(DEFAULT_PROGRESS);
  }
}

export function saveProgress(progress: PlayerProgress): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(progress));
}

export function applyGateRewards(progress: PlayerProgress, rewards: { xp: number; shards: number }): PlayerProgress {
  const updated = { ...progress };
  updated.partnerXp += rewards.xp;
  updated.dataShards += rewards.shards;

  while (updated.partnerXp >= updated.partnerLevel * 100) {
    updated.partnerXp -= updated.partnerLevel * 100;
    updated.partnerLevel += 1;
    updated.playerLevel += 1;
  }

  if (updated.partnerLevel >= 5) updated.partnerForm = "Scout";
  if (updated.partnerLevel >= 10) updated.partnerForm = "Operator";
  if (updated.partnerLevel >= 20) updated.partnerForm = "Architect";

  updated.gateTier = Math.max(updated.gateTier, 1 + Math.floor(updated.partnerLevel / 3));
  updated.chipLevel = Math.max(updated.chipLevel, 1 + Math.floor(updated.partnerLevel / 5));
  updated.buildingLevel = Math.max(updated.buildingLevel, 1 + Math.floor(updated.playerLevel / 4));

  saveProgress(updated);
  return updated;
}
