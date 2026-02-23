# unit.py
# Represents individual units.


class Unit:
    def __init__(self, unit_id):
        self.id = unit_id
        self.state = "idle"
        self.behavior = None
        self.mission_id = None
