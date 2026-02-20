# swarm.py
# Implements the Swarm Engine components.

class Unit:
    def __init__(self, unit_id, capabilities):
        self.unit_id = unit_id
        self.capabilities = capabilities

class UnitRegistry:
    def __init__(self):
        self.units = {}

    def register_unit(self, unit):
        """Register a new unit."""
        self.units[unit.unit_id] = unit

    def get_unit(self, unit_id):
        """Retrieve a unit by ID."""
        return self.units.get(unit_id)

class BehaviorEngine:
    def execute_behavior(self, unit, behavior):
        """Execute a behavior for a unit."""
        return f"Unit {unit.unit_id} executed {behavior}"

class FormationEngine:
    def create_formation(self, units, formation_type):
        """Create a formation with units."""
        return f"Formation {formation_type} created with units {[unit.unit_id for unit in units]}"

# Example usage
if __name__ == "__main__":
    unit1 = Unit("unit1", ["scout"])
    unit2 = Unit("unit2", ["attack"])

    registry = UnitRegistry()
    registry.register_unit(unit1)
    registry.register_unit(unit2)

    behavior_engine = BehaviorEngine()
    formation_engine = FormationEngine()

    print(behavior_engine.execute_behavior(unit1, "scouting"))
    print(formation_engine.create_formation([unit1, unit2], "wedge"))