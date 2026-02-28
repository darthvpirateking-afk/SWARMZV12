import React, { useEffect, useState } from "react";

type EvolutionState = {
  current_form: string;
  next_form: string | null;
  rank: string;
  can_evolve: boolean;
  sovereign_unlocked: boolean;
  monarch_available?: boolean;
};

type CockpitStatusPayload = {
  ok?: boolean;
  evolution?: EvolutionState;
};

const POLL_MS = 5000;

export default function AvatarMode() {
  const [evolution, setEvolution] = useState<EvolutionState | null>(null);
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
        if (!payload.evolution) {
          throw new Error("missing evolution state");
        }
        setEvolution(payload.evolution);
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

  return (
    <section data-mode-id="avatar" aria-label="avatar">
      <h3>Sovereign Avatar</h3>
      {error && <p>status error: {error}</p>}
      {!error && !evolution && <p>loading evolution state...</p>}
      {evolution && (
        <div>
          <p>current_form: {evolution.current_form}</p>
          <p>next_form: {evolution.next_form ?? "none"}</p>
          <p>rank: {evolution.rank}</p>
          <p>evolution_readiness: {evolution.can_evolve ? "ready" : "locked"}</p>
          <p>sovereign: {evolution.sovereign_unlocked ? "unlocked" : "locked"}</p>
          <p>
            monarch_mode: {evolution.monarch_available ? "available" : "unavailable"}
          </p>
        </div>
      )}
    </section>
  );
}
