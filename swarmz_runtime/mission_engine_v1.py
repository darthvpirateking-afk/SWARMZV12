# Mission Engine v1
# This module handles mission parsing, planning, execution, and reporting.

class MissionEngineV1:
    def __init__(self):
        # Initialize mission state
        self.missions = {}

    def create_mission(self, mission_id, name, steps):
        """Create a new mission."""
        self.missions[mission_id] = {
            "id": mission_id,
            "name": name,
            "steps": steps,
            "state": "pending"
        }

    def start_mission(self, mission_id):
        """Start a mission."""
        if mission_id in self.missions:
            self.missions[mission_id]["state"] = "active"

    def complete_mission(self, mission_id):
        """Mark a mission as completed."""
        if mission_id in self.missions:
            self.missions[mission_id]["state"] = "completed"

    def fail_mission(self, mission_id):
        """Mark a mission as failed."""
        if mission_id in self.missions:
            self.missions[mission_id]["state"] = "failed"

    def get_mission_state(self, mission_id):
        """Get the state of a mission."""
        return self.missions.get(mission_id, {}).get("state", "unknown")

    def list_missions(self):
        """List all missions."""
        return self.missions

# Example usage
if __name__ == "__main__":
    engine = MissionEngineV1()
    engine.create_mission("M1", "Explore Sector", ["Step1", "Step2"])
    print("Missions:", engine.list_missions())

    engine.start_mission("M1")
    print("Mission State:", engine.get_mission_state("M1"))

    engine.complete_mission("M1")
    print("Mission State:", engine.get_mission_state("M1"))