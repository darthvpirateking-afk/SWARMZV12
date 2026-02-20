# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""Autoscaling recommendation helpers for infrastructure metrics.

This module consumes the infra overview produced by ``infra_metrics`` and
returns conservative, human-readable recommendations. It does **not**
perform any actions itself; higher layers are expected to translate
these recommendations into missions or external orchestrator calls.
"""

from __future__ import annotations

from typing import Any, Dict, List


def compute_autoscale_recommendations(
    overview: Dict[str, Any],
    target_cpu: float = 0.6,
    max_cpu: float = 0.85,
    min_cpu: float = 0.15,
) -> Dict[str, Any]:
    """Compute simple autoscaling-style hints from an infra overview.

    Rules (intentionally simple and explanation-first):
    - If a node's avg_cpu is >= max_cpu: mark as "hot" and recommend
      adding capacity or shedding load.
    - If avg_cpu is between target_cpu and max_cpu: mark as "warm" and
      steady.
    - If avg_cpu is between min_cpu and target_cpu: mark as "normal".
    - If avg_cpu is < min_cpu: mark as "cold" and a consolidation
      candidate.
    """

    nodes = overview.get("nodes") or []
    if not nodes:
        return {
            "summary": {
                "status": "no_data",
                "reason": "no metrics available",
            },
            "nodes": [],
        }

    plan_nodes: List[Dict[str, Any]] = []
    hot = 0
    cold = 0

    for node in nodes:
        node_id = str(node.get("node_id") or "unknown")
        avg_cpu = node.get("avg_cpu")
        entry: Dict[str, Any] = {"node_id": node_id, "avg_cpu": avg_cpu}

        # Nodes without CPU data are left as "unknown".
        if not isinstance(avg_cpu, (int, float)):
            entry["status"] = "unknown"
            entry["recommendation"] = "collect_more_data"
            entry["reason"] = "no avg_cpu metric present for node"
            plan_nodes.append(entry)
            continue

        if avg_cpu >= max_cpu:
            entry["status"] = "hot"
            entry["recommendation"] = "add_capacity_or_shed_load"
            entry["reason"] = (
                f"avg_cpu={avg_cpu:.2f} exceeds max_cpu={max_cpu:.2f}; "
                "consider scaling up or redistributing workloads"
            )
            hot += 1
        elif avg_cpu >= target_cpu:
            entry["status"] = "warm"
            entry["recommendation"] = "steady"
            entry["reason"] = (
                f"avg_cpu={avg_cpu:.2f} is between target_cpu={target_cpu:.2f} "
                f"and max_cpu={max_cpu:.2f}; monitor but no action required"
            )
        elif avg_cpu < min_cpu:
            entry["status"] = "cold"
            entry["recommendation"] = "consolidate_if_possible"
            entry["reason"] = (
                f"avg_cpu={avg_cpu:.2f} below min_cpu={min_cpu:.2f}; "
                "candidate for consolidation to save power/cost"
            )
            cold += 1
        else:
            entry["status"] = "normal"
            entry["recommendation"] = "steady"
            entry["reason"] = (
                f"avg_cpu={avg_cpu:.2f} within normal operating band "
                f"[{min_cpu:.2f}, {target_cpu:.2f})"
            )

        plan_nodes.append(entry)

    total = len(plan_nodes)
    if hot > 0:
        status = "scale_up_or_shed_load"
        reason = f"{hot} of {total} nodes are hot (>= {max_cpu:.2f} cpu)."
    elif cold > 0 and hot == 0:
        status = "consider_consolidation"
        reason = f"{cold} of {total} nodes are cold (< {min_cpu:.2f} cpu)."
    else:
        status = "steady"
        reason = "all nodes within normal or warm range."

    return {
        "summary": {
            "status": status,
            "reason": reason,
            "total_nodes": total,
            "hot_nodes": hot,
            "cold_nodes": cold,
        },
        "nodes": plan_nodes,
    }

