class EnergyModel:
    def __init__(self):
        self.energy_states = {}

    def compute_energy(self, entity: str, value: float):
        self.energy_states[entity] = value

    def mission_energy(self, mission_id: str, value: float):
        self.compute_energy(f"mission:{mission_id}", value)

    def swarm_energy(self, swarm_id: str, value: float):
        self.compute_energy(f"swarm:{swarm_id}", value)

    def get_energy_state(self):
        return self.energy_states
