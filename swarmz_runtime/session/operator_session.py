class OperatorSession:
    def __init__(self, operator_id: str, session_id: str):
        self.operator_id = operator_id
        self.session_id = session_id
        self.active_mission = None
        self.last_command = None
        self.cockpit_state = {}

    def update_cockpit_state(self, state: dict):
        self.cockpit_state.update(state)

    def log_command(self, command: str):
        self.last_command = command

    def attach_mission(self, mission_id: str):
        self.active_mission = mission_id

    def end_session(self):
        return {
            "operator_id": self.operator_id,
            "session_id": self.session_id,
            "active_mission": self.active_mission,
            "last_command": self.last_command,
            "cockpit_state": self.cockpit_state,
        }