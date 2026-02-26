import { useEffect, useState } from "react";
import { getHealth, getGovernor } from "../api";
import StatusCard from "./StatusCard";
import AvatarPanel from "../avatar/AvatarPanel";

export default function Cockpit() {
  const [health, setHealth] = useState<unknown>(null);
  const [governor, setGovernor] = useState<unknown>(null);

  useEffect(() => {
    getHealth()
      .then(setHealth)
      .catch(() => setHealth({ error: "unavailable" }));
    getGovernor()
      .then(setGovernor)
      .catch(() => setGovernor({ error: "unavailable" }));
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
      <div style={{ gridColumn: "1 / -1" }}>
        <AvatarPanel />
      </div>
    </div>
  );
}
