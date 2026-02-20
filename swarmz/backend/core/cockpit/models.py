# models.py
# Defines cockpit-related models.

class Cockpit:
    def __init__(self, name, systems):
        self.name = name
        self.systems = systems

    def __repr__(self):
        return f"Cockpit(name={self.name}, systems={self.systems})"
