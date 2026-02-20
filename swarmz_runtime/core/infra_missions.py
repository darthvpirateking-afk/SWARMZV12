# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""Simulation-only mission emitter for infra orchestration.

This module converts infra autoscale/backup plans into SWARMZ missions
without touching any real infrastructure. It appends missions to the
standard missions.jsonl log via the runtime Database.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, List

from swarmz_runtime.storage.db import Database
from swarmz_runtime.storage.schema import Mission, MissionCategory, MissionStatus


_db = Database("data")


def _new_mission_id() -> str:
    return str(uuid.uuid4())[:8]


def _save_mission(goal: str, category: MissionCategory, constraints: Dict[str, Any]) -> Mission:
    mission = Mission(
        id=_new_mission_id(),
        goal=goal,
        category=category,
        constraints=constraints,
        status=MissionStatus.PENDING,
    )
    _db.save_mission(mission)
    return mission


def emit_infra_missions(autoscale_plan: Dict[str, Any], backup_plan: Dict[str, Any]) -> Dict[str, Any]:
    """Create simulation-only missions representing infra recommendations.

    The resulting missions are tagged with "infra_simulation": True in
    their constraints so that downstream tools can distinguish them.
    """

    created_ids: List[str] = []

    # Autoscaling-related missions
    for node in autoscale_plan.get("nodes", []) or []:
        status = node.get("status")
        node_id = node.get("node_id") or "unknown"
        base_constraints: Dict[str, Any] = {
            "kind": "infra_autoscale",
            "infra_simulation": True,
            "node": node,
        }

        if status == "hot":
            goal = f"Scale up capacity or shed load for infra node {node_id} based on autoscale_plan."
            mission = _save_mission(goal, MissionCategory.FORGE, base_constraints)
            created_ids.append(mission.id)
        elif status == "cold":
            goal = f"Evaluate consolidation options for infra node {node_id} to save power/cost."
            mission = _save_mission(goal, MissionCategory.SANCTUARY, base_constraints)
            created_ids.append(mission.id)

    # Backup/DR mission (single umbrella mission for now)
    if backup_plan:
        goal = "Establish or review backup/DR schedule for infra resources per backup_plan."
        constraints = {
            "kind": "infra_backup",
            "infra_simulation": True,
            "plan": backup_plan,
        }
        mission = _save_mission(goal, MissionCategory.SANCTUARY, constraints)
        created_ids.append(mission.id)

    return {
        "ok": True,
        "created_missions": len(created_ids),
        "mission_ids": created_ids,
    }

