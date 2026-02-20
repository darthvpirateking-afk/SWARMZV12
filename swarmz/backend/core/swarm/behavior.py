# behavior.py
# Executes unit behaviors.

class BehaviorEngine:
    def execute_behavior(self, unit, behavior):
        """Execute a behavior for a unit."""
        return f"Unit {unit.unit_id} executed {behavior}"

    def apply(self, unit, behavior):
        """Apply a behavior to a unit."""
        unit["behavior"] = behavior
