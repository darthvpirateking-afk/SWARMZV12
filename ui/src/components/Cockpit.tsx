import { useEffect, useState } from "react";
import { getHealth, getGovernor, getCanonicalAgents, getRecentTraces, runHelper1 } from "../api";
import StatusCard from "./StatusCard";
import AvatarPanel from "../avatar/AvatarPanel";

export default function Cockpit() {
  const [health, setHealth] = useState<unknown>(null);
  const [governor, setGovernor] = useState<unknown>(null);
  const [agents, setAgents] = useState<unknown>(null);
  const [traces, setTraces] = useState<unknown>(null);
  const [helperQuery, setHelperQuery] = useState("ping");
  const [helperOut, setHelperOut] = useState<unknown>(null);

  useEffect(() => {
    getHealth()
      .then(setHealth)
      .catch(() => setHealth({ error: "unavailable" }));
    getGovernor()
      .then(setGovernor)
      .catch(() => setGovernor({ error: "unavailable" }));
    getCanonicalAgents()
      .then(setAgents)
      .catch(() => setAgents({ error: "unavailable" }));
    getRecentTraces(20)
      .then(setTraces)
      .catch(() => setTraces({ error: "unavailable" }));
  }, []);

  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "1fr 1fr",
        gridTemplateRows: "auto 1fr",
        gap: 16,
        height: "100%",
      }}
    >
      <StatusCard title="Health" data={health} />
      <StatusCard title="Governor" data={governor} />
      <StatusCard title="Canonical Agents" data={agents} />
      <StatusCard title="Recent Traces" data={traces} />
      <div
        style={{
          border: "1px solid #333",
          padding: 16,
          borderRadius: 8,
          minWidth: 200,
          gridColumn: "1 / -1",
        }}
      >
        <h2>Helper1 Run</h2>
        <div style={{ display: "flex", gap: 8, marginBottom: 8 }}>
          <input
            value={helperQuery}
            onChange={(e) => setHelperQuery(e.target.value)}
            style={{ flex: 1, padding: 8, borderRadius: 6, border: "1px solid #444" }}
          />
          <button
            onClick={() =>
              runHelper1(helperQuery)
                .then((data) => {
                  setHelperOut(data);
                  return getRecentTraces(20).then(setTraces);
                })
                .catch(() => setHelperOut({ error: "run failed" }))
            }
            style={{ padding: "8px 12px", borderRadius: 6, border: "1px solid #444" }}
          >
            Run
          </button>
        </div>
        <pre style={{ fontSize: 12 }}>{helperOut ? JSON.stringify(helperOut, null, 2) : "idle"}</pre>
      </div>
      <div style={{ gridColumn: "1 / -1" }}>
        <AvatarPanel />
      </div>
    </div>
  );
}
