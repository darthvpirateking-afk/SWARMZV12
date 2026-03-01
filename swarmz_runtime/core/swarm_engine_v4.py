# SWARMZ Swarm Engine v4
# Emergent Formations

from typing import Dict, Any, List
import uuid
from datetime import datetime, timezone


class FormationRuleset:
    def __init__(self, rules: Dict[str, Any]):
        self.rules = rules


class FormationSynthesizer:
    def __init__(self):
        self.formations: List[Dict[str, Any]] = []

    def synthesize(self, ruleset: FormationRuleset) -> Dict[str, Any]:
        """Build an emergent formation from a FormationRuleset.

        Produces a formation dict with: id, pattern, units, rules snapshot.
        The pattern is derived from the ruleset's 'pattern' key (default: 'delta').
        """
        rules = ruleset.rules if ruleset else {}
        pattern = rules.get("pattern", "delta")
        unit_count = int(rules.get("unit_count", 3))
        formation: Dict[str, Any] = {
            "id": str(uuid.uuid4())[:8],
            "pattern": pattern,
            "unit_count": unit_count,
            "units": [{"slot": i + 1, "role": rules.get("role", "agent")} for i in range(unit_count)],
            "rules_snapshot": rules,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "SYNTHESIZED",
        }
        self.formations.append(formation)
        return formation


class FormationExecutor:
    def __init__(self):
        self.active_formations: List[Dict[str, Any]] = []

    def execute(self, formation: Dict[str, Any]) -> Dict[str, Any]:
        """Apply a formation pattern to swarm units.

        Marks each unit slot as DEPLOYED and records the formation as active.
        """
        if not formation:
            return {"ok": False, "error": "empty formation"}

        for unit in formation.get("units", []):
            unit["status"] = "DEPLOYED"

        formation["status"] = "ACTIVE"
        formation["activated_at"] = datetime.now(timezone.utc).isoformat()
        self.active_formations.append(formation)

        return {
            "ok": True,
            "formation_id": formation.get("id"),
            "pattern": formation.get("pattern"),
            "units_deployed": len(formation.get("units", [])),
        }


class FormationMonitor:
    def __init__(self):
        self.visualization_data: Dict[str, Any] = {}

    def update_visualization(self, formations: List[Dict[str, Any]]):
        """Update cockpit visualization of emergent patterns."""
        self.visualization_data = {f["id"]: f for f in formations if "id" in f}
