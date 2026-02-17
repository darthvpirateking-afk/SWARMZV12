# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
Drift Scanner â€” detect distribution shift and pause learning when drift is high.
"""

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from addons.config_ext import get_config

_DRIFT_FILE = "addons/data/drift_history.jsonl"


def _audit(event: str, details: dict) -> None:
    cfg = get_config()
    audit_path = Path(cfg.get("audit_file", "data/audit.jsonl"))
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": event,
        "details": details,
    }
    with open(audit_path, "a") as f:
        f.write(json.dumps(entry) + "\n")


def record_metric(name: str, value: float) -> Dict[str, Any]:
    p = Path(_DRIFT_FILE)
    p.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "metric": name,
        "value": value,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    with open(p, "a") as f:
        f.write(json.dumps(entry) + "\n")
    return entry


def compute_drift(name: str, window: int = 20) -> Dict[str, Any]:
    """Compute drift for a metric as |mean_recent - mean_old| / stddev_old."""
    entries = _load_metric(name)
    if len(entries) < window * 2:
        return {"drift": 0.0, "status": "insufficient_data", "n": len(entries)}

    old = entries[-(window * 2):-window]
    recent = entries[-window:]

    old_vals = [e["value"] for e in old]
    new_vals = [e["value"] for e in recent]

    old_mean = sum(old_vals) / len(old_vals)
    new_mean = sum(new_vals) / len(new_vals)
    old_std = max(math.sqrt(sum((v - old_mean) ** 2 for v in old_vals) / len(old_vals)), 1e-9)

    drift = abs(new_mean - old_mean) / old_std

    cfg = get_config()
    threshold = cfg.get("drift_threshold", 0.25)
    high = drift > threshold

    result = {"metric": name, "drift": round(drift, 4), "threshold": threshold, "high": high}

    if high:
        _audit("drift_detected", result)

    return result


def _load_metric(name: str) -> List[Dict[str, Any]]:
    p = Path(_DRIFT_FILE)
    if not p.exists():
        return []
    entries: List[Dict[str, Any]] = []
    with open(p) as f:
        for line in f:
            if line.strip():
                e = json.loads(line)
                if e.get("metric") == name:
                    entries.append(e)
    return entries


def scan_all_metrics() -> List[Dict[str, Any]]:
    """Scan all recorded metrics for drift."""
    p = Path(_DRIFT_FILE)
    if not p.exists():
        return []
    names: set = set()
    with open(p) as f:
        for line in f:
            if line.strip():
                e = json.loads(line)
                names.add(e.get("metric", ""))
    return [compute_drift(n) for n in sorted(names) if n]

