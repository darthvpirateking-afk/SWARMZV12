import React, { useEffect, useState } from 'react';

interface HologramData {
  personality: string;
  phase: string;
  entropy: number;
  operator_binding: string;
  trajectory: string;
  last_mission: string;
}

const MasterSwarmzHologram = () => {
  const [hologramData, setHologramData] = useState<HologramData | null>(null);

  useEffect(() => {
    fetch('/v1/companion/hologram')
      .then((response) => response.json())
      .then((data: HologramData) => setHologramData(data))
      .catch((error) => console.error('Error fetching hologram data:', error));
  }, []);

  if (!hologramData) {
    return <div>Loading...</div>;
  }

  return (
    <div className="hologram-panel">
      <h2>Hologram Panel</h2>
      <p><strong>Personality Traits:</strong> {hologramData.personality}</p>
      <p><strong>Phase:</strong> {hologramData.phase}</p>
      <p><strong>Entropy:</strong> {hologramData.entropy}</p>
      <p><strong>Operator Binding:</strong> {hologramData.operator_binding}</p>
      <p><strong>Trajectory:</strong> {hologramData.trajectory}</p>
      <p><strong>Last Mission:</strong> {hologramData.last_mission}</p>
    </div>
  );
};

export default MasterSwarmzHologram;