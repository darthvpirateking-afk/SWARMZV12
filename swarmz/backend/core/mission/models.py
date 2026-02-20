# Models module for SWARMZ mission

class Models:
    pass

class Mission:
    def __init__(self, mission_id, name, steps):
        self.id = mission_id
        self.name = name
        self.steps = steps
        self.state = "pending"

    def __repr__(self):
        return f"Mission(id={self.id}, name={self.name}, state={self.state})"
