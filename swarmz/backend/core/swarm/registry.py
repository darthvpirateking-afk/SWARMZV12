# registry.py
# Manages unit registration.


class UnitRegistry:
    def __init__(self):
        self.units = {}

    def register(self, unit):
        """Register a new unit."""
        self.units[unit.id] = unit

    def get(self, unit_id):
        """Retrieve a unit by ID."""
        return self.units.get(unit_id)
