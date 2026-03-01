import React, { useEffect, useMemo, useState } from "react";

type EvolutionState = {
  current_form: string;
  next_form: string | null;
  rank: string;
  can_evolve: boolean;
  sovereign_unlocked: boolean;
  monarch_available: boolean;
};

type SummonState = {
  id: string;
  name?: string;
  tier: string;
  aura: string;
  form_required?: string;
  stats?: Record<string, number>;
  last_command?: string;
};

type AbilityState = {
  unlocked?: string[];
  combat_profile?: Record<string, number | string | string[]>;
};

type ChipEntry = {
  id: string;
  category: string;
  min_form?: string;
  visual_effect?: string;
  stats?: Record<string, number>;
  evolution_modifiers?: Record<string, Record<string, number>>;
  monarch_modifiers?: Record<string, number>;
};

type ChipState = {
  available?: ChipEntry[];
  locked?: ChipEntry[];
  categories?: Record<string, ChipEntry[]>;
  recent_executions?: Array<Record<string, unknown>>;
};

type CockpitStatusPayload = {
  ok?: boolean;
  evolution?: EvolutionState;
  monarch_mode?: boolean;
  active_summons?: SummonState[];
  abilities?: AbilityState;
  chip_state?: ChipState;
};

const POLL_MS = 5000;

export default function AvatarMode() {
  const [status, setStatus] = useState<CockpitStatusPayload | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;

    const load = async () => {
      try {
        const res = await fetch("/cockpit/status");
        if (!res.ok) {
          throw new Error(`status ${res.status}`);
        }
        const payload = (await res.json()) as CockpitStatusPayload;
        if (!mounted) {
          return;
        }
        setStatus(payload);
        setError(null);
      } catch (err) {
        if (!mounted) {
          return;
        }
        setError(err instanceof Error ? err.message : "failed to load cockpit status");
      }
    };

    void load();
    const id = window.setInterval(() => void load(), POLL_MS);
    return () => {
      mounted = false;
      window.clearInterval(id);
    };
  }, []);

  const evolution = status?.evolution ?? null;
  const summons = status?.active_summons ?? [];
  const abilities = status?.abilities ?? {};
  const chipState = status?.chip_state ?? {};
  const monarchMode = Boolean(status?.monarch_mode);

  const categories = useMemo(() => chipState.categories ?? {}, [chipState.categories]);
  const available = chipState.available ?? [];
  const locked = chipState.locked ?? [];
  const recentExecutions = chipState.recent_executions ?? [];

  return (
    <section data-mode-id="avatar" aria-label="avatar">
      <h3>Sovereign Avatar</h3>
      <img src="/assets/my-avatar.png" alt="Sovereign Avatar" style={{ width: 96, height: 96, borderRadius: "50%" }} />
      {error && <p>status error: {error}</p>}
      {!error && !evolution && <p>loading avatar state...</p>}

      {evolution && (
        <div>
          <h4>Evolution</h4>
          <p>current_form: {evolution.current_form}</p>
          <p>next_form: {evolution.next_form ?? "none"}</p>
          <p>rank: {evolution.rank}</p>
          <p>evolution_readiness: {evolution.can_evolve ? "ready" : "locked"}</p>
          <p>sovereign: {evolution.sovereign_unlocked ? "unlocked" : "locked"}</p>
          <p>monarch_availability: {evolution.monarch_available ? "available" : "unavailable"}</p>
        </div>
      )}

      <div>
        <h4>Monarch</h4>
        <p>mode: {monarchMode ? "ACTIVE" : "INACTIVE"}</p>
        <p>aura: {monarchMode ? "shadow-cosmic" : "dormant"}</p>
      </div>

      <div>
        <h4>Monarch Summons</h4>
        {summons.length === 0 ? (
          <p>none</p>
        ) : (
          <ul>
            {summons.map((summon) => (
              <li key={summon.id}>
                {summon.id} | tier={summon.tier} | aura={summon.aura} | requires=
                {summon.form_required ?? "AvatarOmega"} | stats=
                {summon.stats ? JSON.stringify(summon.stats) : "{}"}
              </li>
            ))}
          </ul>
        )}
      </div>

      <div>
        <h4>Abilities</h4>
        <p>
          unlocked: {Array.isArray(abilities.unlocked) && abilities.unlocked.length > 0
            ? abilities.unlocked.join(", ")
            : "none"}
        </p>
      </div>

      <div>
        <h4>Battle Chips</h4>
        <p>available: {available.length}</p>
        <p>locked: {locked.length}</p>
        {available.length > 0 && (
          <div>
            <p>available chips:</p>
            <ul>
              {available.map((chip) => (
                <li key={`available-${chip.id}`}>
                  {chip.id} [{chip.category}] min_form={chip.min_form ?? "AvatarOmega"} dmg=
                  {chip.stats?.base_damage ?? 0} spd={chip.stats?.base_speed ?? 0} cost=
                  {chip.stats?.base_cost ?? 0}
                </li>
              ))}
            </ul>
          </div>
        )}
        {locked.length > 0 && (
          <div>
            <p>locked chips:</p>
            <ul>
              {locked.map((chip) => (
                <li key={`locked-${chip.id}`}>
                  {chip.id} [{chip.category}] requires={chip.min_form ?? "AvatarOmega"}
                </li>
              ))}
            </ul>
          </div>
        )}
        {Object.keys(categories).length > 0 && (
          <ul>
            {Object.entries(categories).map(([name, chips]) => (
              <li key={name}>
                {name}: {chips.length}
              </li>
            ))}
          </ul>
        )}
        {monarchMode && <p>monarch modifiers: +50% damage, +25% speed</p>}
        {recentExecutions.length > 0 && (
          <div>
            <p>recent executions:</p>
            <ul>
              {recentExecutions.slice(-5).map((entry, index) => (
                <li key={index}>{JSON.stringify(entry)}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </section>
  );
}
