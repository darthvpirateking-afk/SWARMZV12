from __future__ import annotations

from typing import Any, Dict


def safety_assess(proposal: Dict[str, Any]) -> Dict[str, Any]:
    risk = proposal["risk"]
    ptype = proposal["type"]
    diff = proposal.get("diff", {})

    flags = []

    if risk == "high":
        flags.append("requires-multi-approval")

    if diff.get("kind") == "file" and "delete" in diff.get("content_hint", "").lower():
        flags.append("potential-destructive-change")

    if ptype == "backend" and risk != "high":
        flags.append("backend-modules-should-be-high-risk")

    return {"safe": len(flags) == 0, "flags": flags, "summary": "Safety evaluation completed."}
