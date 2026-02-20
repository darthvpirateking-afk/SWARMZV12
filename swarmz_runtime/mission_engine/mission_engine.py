class MissionEngine:
    def __init__(self):
        self.missions = {}

    def add_mission(self, mission_id, mission_type, steps):
        self.missions[mission_id] = {
            "type": mission_type,
            "steps": steps,
            "state": "pending",
        }

    def start_mission(self, mission_id):
        if mission_id in self.missions:
            self.missions[mission_id]["state"] = "active"
            return f"Mission {mission_id} started."
        return f"Mission {mission_id} not found."

    def complete_mission(self, mission_id):
        if mission_id in self.missions:
            self.missions[mission_id]["state"] = "completed"
            return f"Mission {mission_id} completed."
        return f"Mission {mission_id} not found."

    def get_mission_state(self, mission_id):
        return self.missions.get(mission_id, {}).get("state", "Mission not found.")