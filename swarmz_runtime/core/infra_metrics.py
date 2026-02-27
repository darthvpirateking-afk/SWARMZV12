# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""Infrastructure metrics ingestion and overview helpers.

This module is intentionally thin: it records infra metrics as events in the
append-only infra log and can build a simple overview for API consumers.

It does not perform any orchestration on its own; higher layers translate
these summaries into missions or external actions.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List

from swarmz_runtime.storage.infra_state import append_infra_event, load_infra_events

_METRIC_FIELDS = ("cpu", "memory", "gpu", "disk", "net_rx", "net_tx")


def record_infra_metrics(sample: Dict[str, Any]) -> None:
    """Normalize and append a single infra metrics sample.

    Expected keys include:
    - node_id: stable identifier for the node
    - cpu, memory, gpu, disk, net_rx, net_tx: floats or ints
    - ts: optional ISO8601 timestamp; if missing, filled in with now()
    """

    node_id = str(sample.get("node_id") or sample.get("id") or "unknown")
    ts = sample.get("ts") or datetime.now(timezone.utc).isoformat()

    payload: Dict[str, Any] = {}
    for field in _METRIC_FIELDS:
        if field in sample:
            payload[field] = sample[field]

    event: Dict[str, Any] = {
        "type": "metrics",
        "ts": ts,
        "node_id": node_id,
        "payload": payload,
    }

    # Preserve any extra attributes under a dedicated key for debuggability.
    extras = {
        k: v
        for k, v in sample.items()
        if k not in {"node_id", "id", "ts"} and k not in _METRIC_FIELDS
    }
    if extras:
        event["extras"] = extras

    append_infra_event(event)


def build_infra_overview(limit: int = 500) -> Dict[str, Any]:
    """Return a coarse infra overview from recent metrics events.

    The overview is intentionally simple and conservative: it computes
    per-node averages across the metrics present in the last *limit*
    events and reports a few high-level aggregates.
    """

    limit = max(1, min(limit, 5000))
    events = load_infra_events(limit=limit)
    metrics = [e for e in events if e.get("type") == "metrics"]
    if not metrics:
        return {"nodes": [], "total_nodes": 0, "last_ts": None}

    per_node: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    last_ts: str | None = None
    for ev in metrics:
        node_id = str(ev.get("node_id") or "unknown")
        payload = ev.get("payload") or {}
        per_node[node_id].append(payload)
        ts = ev.get("ts")
        if isinstance(ts, str):
            last_ts = ts if last_ts is None or ts > last_ts else last_ts

    nodes_summary: List[Dict[str, Any]] = []
    for node_id, samples in per_node.items():
        agg: Dict[str, Any] = {"node_id": node_id, "samples": len(samples)}
        for field in _METRIC_FIELDS:
            values = [
                s[field] for s in samples if isinstance(s.get(field), (int, float))
            ]
            if values:
                agg[f"avg_{field}"] = sum(values) / len(values)
        nodes_summary.append(agg)

    nodes_summary.sort(key=lambda n: n["node_id"])
    return {
        "nodes": nodes_summary,
        "total_nodes": len(nodes_summary),
        "last_ts": last_ts,
    }
