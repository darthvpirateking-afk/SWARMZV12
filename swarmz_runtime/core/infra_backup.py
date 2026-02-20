# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""Backup and disaster-recovery planning helpers for infra state.

This module inspects the materialized infra state snapshot and returns
simple, human-readable backup recommendations. It does **not** perform
any scheduling or I/O; higher layers must translate plans into concrete
backup jobs or DR workflows.
"""

from __future__ import annotations

from typing import Any, Dict, List


_RESOURCE_KEYS = ("servers", "nodes", "vms", "containers", "databases")


def _extract_resources(state: Dict[str, Any]) -> List[Dict[str, Any]]:
    resources: List[Dict[str, Any]] = []
    for key in _RESOURCE_KEYS:
        items = state.get(key)
        if not isinstance(items, list):
            continue
        for raw in items:
            if not isinstance(raw, dict):
                continue
            rid = str(raw.get("id") or raw.get("name") or raw.get("node_id") or "unknown")
            resources.append({"id": rid, "kind": key.rstrip("s") or key})
    return resources


def compute_backup_plan(state: Dict[str, Any], default_interval_hours: int = 24) -> Dict[str, Any]:
    """Compute a conservative backup/DR plan from infra state.

    The goal is to produce an explanation-first summary rather than a
    low-level job spec. If the state is empty or unstructured, the
    function falls back to generic guidance.
    """

    if not isinstance(state, dict) or not state:
        return {
            "summary": {
                "status": "no_state",
                "reason": "no infra_state snapshot present; recommend capturing current topology before planning backups",
            },
            "resources": [],
            "schedule": None,
        }

    resources = _extract_resources(state)
    if not resources:
        return {
            "summary": {
                "status": "unknown_topology",
                "reason": "infra_state present but no known resource lists (servers/nodes/vms/containers/databases)",
            },
            "resources": [],
            "schedule": {
                "interval_hours": default_interval_hours,
                "retention_days": 7,
                "replication_copies": 2,
            },
        }

    total = len(resources)
    critical = [r for r in resources if "db" in r["kind"] or "database" in r["kind"]]

    if critical:
        schedule = {
            "interval_hours": min(6, default_interval_hours),
            "retention_days": 14,
            "replication_copies": 3,
        }
        reason = (
            f"{len(critical)} critical data resources detected out of {total}; "
            "recommend more frequent backups with higher retention and replication."
        )
    else:
        schedule = {
            "interval_hours": default_interval_hours,
            "retention_days": 7,
            "replication_copies": 2,
        }
        reason = (
            f"{total} resources detected with no explicit databases; "
            "daily backups with moderate retention are sufficient as a baseline."
        )

    return {
        "summary": {
            "status": "plan_recommended",
            "reason": reason,
            "total_resources": total,
            "critical_resources": len(critical),
        },
        "resources": resources,
        "schedule": schedule,
    }

