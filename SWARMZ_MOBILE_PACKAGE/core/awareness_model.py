# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
SWARMZ Awareness Module â€” live system-state map (read-only).

Converts missions.jsonl + audit.jsonl into a normalized event stream and
lightweight topology for visualization:

- missions -> nodes
- shared resources -> edges
- frequency -> node size
- risk/pressure -> node heat

This module is pure compute: it only reads local JSONL/JSON files and
never mutates runtime state. All writes are append-only audit entries in
its own log file for observability.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from jsonl_utils import read_jsonl
from core.atomic import atomic_append_jsonl

# Root paths
ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
MISSIONS_FILE = DATA_DIR / "missions.jsonl"
AUDIT_FILE = DATA_DIR / "audit.jsonl"
AWARENESS_LOG = DATA_DIR / "audit_awareness.jsonl"


# â”€â”€ Config / thresholds â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

AWARENESS_CONFIG: Dict[str, Any] = {
    "instability_window": 20,  # how many recent missions to consider
    "instability_quarantine_rate": 0.3,
    "coupling_min_shared": 2,  # how many missions per resource to flag coupling
    "bounded_window": 20,  # how many recent missions to inspect for stagnation
}


# â”€â”€ Schema helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

EVENT_FIELDS = (
    "event_id",
    "timestamp",
    "mission_id",
    "action_type",
    "risk_score",
    "duration",
    "result",
    "resource_cost",
    "parent_relation",
)


@dataclass
class NormalizedEvent:
    event_id: str
    timestamp: str
    mission_id: str
    action_type: str
    risk_score: float
    duration: float
    result: str
    resource_cost: float
    parent_relation: str

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        # Keep only expected fields, in a stable order
        return {k: d[k] for k in EVENT_FIELDS}


# â”€â”€ Low-level loaders (read-only) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


def _load_missions() -> List[Dict[str, Any]]:
    rows, _, _ = read_jsonl(MISSIONS_FILE)
    return rows


def _load_audit_events() -> List[Dict[str, Any]]:
    rows, _, _ = read_jsonl(AUDIT_FILE)
    return rows


# â”€â”€ Normalization â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


def _safe_iso(ts: str | None) -> str:
    if not ts:
        return datetime.now(timezone.utc).isoformat()
    return ts


def _risk_from_status(status: str) -> float:
    status = (status or "").upper()
    if status == "FAILURE":
        return 1.0
    if status == "RUNNING":
        return 0.6
    if status == "PENDING":
        return 0.3
    if status == "SUCCESS":
        return 0.1
    return 0.2


def normalize_events() -> List[Dict[str, Any]]:
    """Normalize missions + audit entries into a common event schema.

    This function is deterministic for a given missions/audit snapshot.
    """
    missions = _load_missions()
    audit_events = _load_audit_events()

    out: List[Dict[str, Any]] = []

    # Missions become coarse events
    for m in missions:
        mid = str(m.get("mission_id") or "").strip()
        if not mid:
            continue
        status = m.get("status", "UNKNOWN")
        created = _safe_iso(m.get("created_at") or m.get("timestamp"))
        category = str(m.get("category") or m.get("scope") or "mission")
        resource_cost = float(m.get("estimated_cost", 0.0))

        ev = NormalizedEvent(
            event_id=f"mission:{mid}",
            timestamp=created,
            mission_id=mid,
            action_type=category,
            risk_score=_risk_from_status(status),
            duration=float(m.get("duration", 0.0)),
            result=status,
            resource_cost=resource_cost,
            parent_relation="root",
        )
        out.append(ev.to_dict())

    # Audit entries that have a mission_id become fine-grained events
    for row in audit_events:
        mid = row.get("mission_id")
        if not mid:
            continue
        ts = _safe_iso(row.get("timestamp"))
        action_type = str(row.get("event") or row.get("event_type") or "audit")
        ev = NormalizedEvent(
            event_id=str(row.get("event_id") or f"audit:{mid}:{ts}"),
            timestamp=ts,
            mission_id=str(mid),
            action_type=action_type,
            risk_score=_risk_from_status(str(row.get("result") or "")),
            duration=float(row.get("duration", 0.0)),
            result=str(row.get("result") or row.get("status") or ""),
            resource_cost=float(row.get("cost", 0.0)),
            parent_relation=str(row.get("parent_relation") or ""),
        )
        out.append(ev.to_dict())

    # Sort by time for downstream windowed analysis
    out.sort(key=lambda e: e["timestamp"])
    return out


# â”€â”€ Topology model â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


def build_topology() -> Dict[str, Any]:
    """Build a lightweight topology from normalized events.

    Returns a dict with:
      {
        "nodes": [ {mission_id, size, risk, status, last_event_at, resources} ],
        "edges": [ {source, target, resource, weight} ],
        "meta": {"total_events": int, "total_missions": int}
      }
    """
    events = normalize_events()

    nodes: Dict[str, Dict[str, Any]] = {}
    resources_map: Dict[str, List[str]] = {}

    for ev in events:
        mid = ev["mission_id"]
        node = nodes.setdefault(
            mid,
            {
                "mission_id": mid,
                "size": 0,
                "risk": [],
                "status": ev.get("result") or "",
                "last_event_at": ev["timestamp"],
                "resources": set(),
            },
        )

        node["size"] += 1
        node["risk"].append(ev.get("risk_score", 0.0))
        node["last_event_at"] = max(node["last_event_at"], ev["timestamp"])

        # Treat action_type as a coarse resource label
        resource = ev.get("action_type") or "mission"
        node["resources"].add(resource)
        resources_map.setdefault(resource, []).append(mid)

    # Finalize node metrics
    for node in nodes.values():
        risks = node.pop("risk") or [0.0]
        node["risk"] = float(statistics.fmean(risks))
        node["resources"] = sorted(node["resources"])

    # Build edges based on shared resources
    edges: List[Dict[str, Any]] = []
    for resource, mids in resources_map.items():
        uniq = sorted(set(mids))
        if len(uniq) < 2:
            continue
        # Fully connect missions sharing this resource
        for i, src in enumerate(uniq):
            for dst in uniq[i + 1 :]:
                edges.append(
                    {
                        "source": src,
                        "target": dst,
                        "resource": resource,
                        "weight": 1.0,
                    }
                )

    topology = {
        "nodes": list(nodes.values()),
        "edges": edges,
        "meta": {
            "total_events": len(events),
            "total_missions": len(nodes),
        },
    }
    return topology


# â”€â”€ Alerts / pressure model â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


def compute_alerts(topology: Dict[str, Any]) -> Dict[str, Any]:
    """Compute read-only warning flags from a topology snapshot."""
    nodes = topology.get("nodes", [])
    meta = topology.get("meta", {})

    total_missions = int(meta.get("total_missions", 0))
    # Derive synthetic success rate from node status distribution
    successes = sum(1 for n in nodes if str(n.get("status")).upper() == "SUCCESS")
    failures = sum(1 for n in nodes if str(n.get("status")).upper() == "FAILURE")
    recent_total = successes + failures or total_missions or 1
    success_rate = successes / recent_total if recent_total > 0 else 0.0

    # Instability: mirrors QUARANTINE logic from swarmz_server.compute_phase
    variance_rising = False
    if (
        total_missions >= 10
        and success_rate < AWARENESS_CONFIG["instability_quarantine_rate"]
    ):
        variance_rising = True

    # Coupling: detect resources shared by many missions
    resource_counts: Dict[str, int] = {}
    for n in nodes:
        for r in n.get("resources", []):
            resource_counts[r] = resource_counts.get(r, 0) + 1
    coupling_resources = [
        r
        for r, c in resource_counts.items()
        if c >= AWARENESS_CONFIG["coupling_min_shared"]
    ]
    coupling_detected = bool(coupling_resources)

    # Bounded results: many missions but almost no SUCCESS
    bounded_results = (
        total_missions >= AWARENESS_CONFIG["bounded_window"] and successes == 0
    )

    return {
        "variance_rising": variance_rising,
        "coupling_detected": coupling_detected,
        "bounded_results": bounded_results,
        "success_rate": success_rate,
        "total_missions": total_missions,
        "coupling_resources": coupling_resources,
    }


# â”€â”€ Self-check / audit helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


def _audit(event: str, payload: Dict[str, Any]) -> None:
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": event,
        "payload": payload,
    }
    atomic_append_jsonl(AWARENESS_LOG, entry)


def self_check() -> Dict[str, Any]:
    """Lightweight self-check for wiring + schema.

    Does not mutate runtime data; only appends an entry to the
    module-specific awareness log for observability.
    """
    topo = build_topology()
    alerts = compute_alerts(topo)

    sample_node = topo["nodes"][0] if topo.get("nodes") else None

    payload = {
        "meta": topo.get("meta", {}),
        "alerts": alerts,
        "sample_node_id": sample_node.get("mission_id") if sample_node else None,
    }
    _audit("awareness_self_check", payload)

    return {"ok": True, **payload}
