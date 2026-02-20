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
const FORMS: PartnerForm[] = ["Seed", "Scout", "Operator", "Architect"];
const ROLES: ArmyRole[] = ["Tank", "DPS", "Support", "Specialist"];
const RARITIES: ArmyUnit["rarity"][] = ["Common", "Rare", "Epic", "Legendary"];

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

function getStorage(): Storage | null {
  try {
    if (typeof window === "undefined") return null;
    return window.localStorage;
  } catch {
    return null;
  }
}

function toInt(value: unknown, fallback: number, min = 0): number {
  if (typeof value !== "number" || !Number.isFinite(value)) return fallback;
  return Math.max(min, Math.floor(value));
}

function sanitizeArmy(army: unknown): ArmyUnit[] {
  if (!Array.isArray(army) || army.length === 0) return structuredClone(DEFAULT_PROGRESS.army);

  const cleaned = army
    .map((item): ArmyUnit | null => {
      if (!item || typeof item !== "object") return null;
      const unit = item as Partial<ArmyUnit>;
      return {
        id: typeof unit.id === "string" && unit.id.length > 0 ? unit.id : `unit-${Math.random().toString(16).slice(2, 8)}`,
        role: ROLES.includes(unit.role as ArmyRole) ? (unit.role as ArmyRole) : "DPS",
        rarity: RARITIES.includes(unit.rarity as ArmyUnit["rarity"]) ? (unit.rarity as ArmyUnit["rarity"]) : "Common",
        level: toInt(unit.level, 1, 1),
      };
    })
    .filter((unit): unit is ArmyUnit => unit !== null);

  return cleaned.length > 0 ? cleaned : structuredClone(DEFAULT_PROGRESS.army);
}

function sanitizeProgress(parsed: Partial<PlayerProgress>): PlayerProgress {
  const partnerLevel = toInt(parsed.partnerLevel, DEFAULT_PROGRESS.partnerLevel, 1);

  return {
    playerLevel: toInt(parsed.playerLevel, DEFAULT_PROGRESS.playerLevel, 1),
    partnerLevel,
    partnerForm: FORMS.includes(parsed.partnerForm as PartnerForm) ? (parsed.partnerForm as PartnerForm) : DEFAULT_PROGRESS.partnerForm,
    partnerXp: toInt(parsed.partnerXp, DEFAULT_PROGRESS.partnerXp, 0),
    army: sanitizeArmy(parsed.army),
    chipLevel: toInt(parsed.chipLevel, DEFAULT_PROGRESS.chipLevel, 1),
    buildingLevel: toInt(parsed.buildingLevel, DEFAULT_PROGRESS.buildingLevel, 1),
    gateTier: toInt(parsed.gateTier, DEFAULT_PROGRESS.gateTier, 1),
    dataShards: toInt(parsed.dataShards, DEFAULT_PROGRESS.dataShards, 0),
  };
}

export function loadProgress(): PlayerProgress {
  try {
    const storage = getStorage();
    if (!storage) return structuredClone(DEFAULT_PROGRESS);
    const raw = storage.getItem(STORAGE_KEY);
    if (!raw) return structuredClone(DEFAULT_PROGRESS);
    const parsed = JSON.parse(raw) as Partial<PlayerProgress>;
    return sanitizeProgress(parsed);
  } catch {
    return structuredClone(DEFAULT_PROGRESS);
  }
}

export function saveProgress(progress: PlayerProgress): void {
  const storage = getStorage();
  if (!storage) return;
  storage.setItem(STORAGE_KEY, JSON.stringify(sanitizeProgress(progress)));
}

export function resetProgress(): PlayerProgress {
  const storage = getStorage();
  if (storage) {
    storage.removeItem(STORAGE_KEY);
  }
  return structuredClone(DEFAULT_PROGRESS);
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
