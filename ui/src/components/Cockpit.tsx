import { useEffect, useState } from "react";
import { getHealth, getGovernor } from "../api";
import StatusCard from "./StatusCard";
import AvatarPanel from '../avatar/AvatarPanel';

export default function Cockpit() {
  const [health, setHealth] = useState(null);
  const [governor, setGovernor] = useState(null);

  useEffect(() => {
    getHealth().then(setHealth);
    getGovernor().then(setGovernor);
  }, []);

  return (
    <div style={{ display: "flex", gap: 20 }}>
      <StatusCard title="Health" data={health} />
      <StatusCard title="Governor" data={governor} />
      <AvatarPanel />
    </div>
  );
}
