from __future__ import annotations

from typing import Any, Dict, List


def simulate_proposal(proposal: Dict[str, Any]) -> Dict[str, Any]:
    ptype = proposal["type"]
    risk = proposal["risk"]
    impacts: List[str] = []
    warnings: List[str] = []

    if ptype == "test":
        impacts.append("Improves regression coverage.")
    if ptype == "plugin":
        impacts.append("Adds new extension point.")
    if ptype == "backend":
        impacts.append("Introduces new API surface.")

    if risk == "high":
        warnings.append("High-risk change; ensure multi-approval and tests.")
    return {
        "impacts": impacts,
        "warnings": warnings,
        "summary": "Rule-based simulation of likely impact.",
    }
