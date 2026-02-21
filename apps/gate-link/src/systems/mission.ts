export interface MissionReward {
  xp: number;
  shards: number;
}

export interface GateMission {
  id: string;
  gateType: "Normal" | "Elite" | "Boss" | "Resource";
  durationSeconds: number;
  tier: number;
}

export function createMission(tier: number): GateMission {
  const types: GateMission["gateType"][] = [
    "Normal",
    "Elite",
    "Boss",
    "Resource",
  ];
  const gateType = types[Math.floor(Math.random() * types.length)];
  const baseDuration =
    gateType === "Boss" ? 180 : gateType === "Elite" ? 120 : 90;

  return {
    id: `gate-${Date.now()}`,
    gateType,
    durationSeconds: baseDuration,
    tier,
  };
}

export function resolveMissionReward(mission: GateMission): MissionReward {
  const multiplier =
    mission.gateType === "Boss"
      ? 2.2
      : mission.gateType === "Elite"
        ? 1.6
        : mission.gateType === "Resource"
          ? 1.3
          : 1;
  return {
    xp: Math.round((20 + mission.tier * 6) * multiplier),
    shards: Math.round((15 + mission.tier * 8) * multiplier),
  };
}
