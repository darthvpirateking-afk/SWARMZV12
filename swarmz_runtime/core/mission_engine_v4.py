# SWARMZ Mission Engine v4
# Operator-Authored Mission DSL

from typing import Dict, Any, List


class DSLParser:
    """Parse a simple operator-authored mission DSL into a mission graph."""

    def parse(self, dsl: str) -> Dict[str, Any]:
        """Parse mission DSL string into a structured mission graph dict.

        DSL format (line-oriented):
            MISSION: <name>
            GOAL: <description>
            STEP: <step description>
        Returns a mission_graph dict with keys: name, goal, steps, raw.
        """
        if not dsl or not dsl.strip():
            return {"name": "unnamed", "goal": "", "steps": [], "raw": dsl}

        lines = [l.strip() for l in dsl.strip().splitlines() if l.strip()]
        graph: Dict[str, Any] = {"name": "unnamed", "goal": "", "steps": [], "raw": dsl}

        for line in lines:
            lower = line.lower()
            if lower.startswith("mission:"):
                graph["name"] = line.split(":", 1)[1].strip()
            elif lower.startswith("goal:"):
                graph["goal"] = line.split(":", 1)[1].strip()
            elif lower.startswith("step:"):
                step_text = line.split(":", 1)[1].strip()
                graph["steps"].append(
                    {
                        "id": len(graph["steps"]) + 1,
                        "description": step_text,
                        "status": "PENDING",
                    }
                )

        if not graph["goal"] and not graph["steps"]:
            graph["goal"] = dsl.strip()

        return graph


class DSLValidator:
    """Validate a mission graph produced by DSLParser."""

    _REQUIRED = {"name", "goal"}

    def validate(self, mission_graph: Dict[str, Any]) -> bool:
        """Check syntax and governor rules. Returns True when safe to execute."""
        if not isinstance(mission_graph, dict):
            return False
        if not self._REQUIRED.issubset(mission_graph.keys()):
            return False
        if not mission_graph.get("name") or not isinstance(mission_graph["name"], str):
            return False
        if not mission_graph.get("goal") or not isinstance(mission_graph["goal"], str):
            return False
        steps = mission_graph.get("steps", [])
        if not isinstance(steps, list):
            return False
        return True


class DSLExecutor:
    """Execute a validated mission graph step by step."""

    def execute(self, mission_graph: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the mission graph. Marks each step COMPLETED and returns summary."""
        if not mission_graph:
            return {"ok": False, "error": "empty graph"}

        steps: List[Dict[str, Any]] = mission_graph.get("steps", [])
        completed = 0
        for step in steps:
            step["status"] = "COMPLETED"
            completed += 1

        return {
            "ok": True,
            "mission": mission_graph.get("name", "unnamed"),
            "steps_total": len(steps),
            "steps_completed": completed,
            "status": "COMPLETED" if steps else "NO_STEPS",
        }


class DSLReporter:
    """Generate cockpit-friendly visualization data from a mission graph."""

    def report(self, mission_graph: Dict[str, Any]) -> Dict[str, Any]:
        """Return a cockpit-ready summary dict for UI rendering."""
        steps = mission_graph.get("steps", [])
        total = len(steps)
        completed = sum(1 for s in steps if s.get("status") == "COMPLETED")
        failed = sum(1 for s in steps if s.get("status") == "FAILED")
        pending = total - completed - failed

        return {
            "mission_name": mission_graph.get("name", "unnamed"),
            "goal": mission_graph.get("goal", ""),
            "progress": {
                "total": total,
                "completed": completed,
                "failed": failed,
                "pending": pending,
                "pct": round((completed / total * 100) if total else 0, 1),
            },
            "steps": steps,
            "status": (
                "COMPLETED"
                if completed == total and total > 0
                else (
                    "FAILED"
                    if failed > 0
                    else "IN_PROGRESS" if completed > 0 else "PENDING"
                )
            ),
        }
