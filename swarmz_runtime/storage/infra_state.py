# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""Append-only infra state storage helpers.

This module mirrors the append-only JSONL pattern used elsewhere in
SWARMZ (missions, audit, trials).  It provides a minimal event log and a
materialized view for infrastructure resources.

It is intentionally not wired into the runtime by default; higher layers
must opt in via configuration before using it.
"""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Dict, List

DATA_DIR = Path("data")
DATA_DIR.mkdir(parents=True, exist_ok=True)

INFRA_EVENTS_PATH = DATA_DIR / "infra_events.jsonl"
INFRA_STATE_PATH = DATA_DIR / "infra_state.json"


def _to_dict(obj: Any) -> Any:
    """Best-effort conversion of dataclasses and simple objects to dicts."""

    if is_dataclass(obj):
        return asdict(obj)
    return obj


def append_infra_event(event: Dict[str, Any]) -> None:
    """Append a single infrastructure event to the JSONL log.

    The caller is responsible for choosing event structure; typically this
    will include a `type` field plus resource identifiers and payload.
    """

    INFRA_EVENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with INFRA_EVENTS_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, separators=(",", ":")) + "\n")


def load_infra_events(limit: int | None = None) -> List[Dict[str, Any]]:
    """Load infrastructure events from the JSONL log.

    If limit is provided, return only the last N events.
    """

    if not INFRA_EVENTS_PATH.exists():
        return []
    with INFRA_EVENTS_PATH.open("r", encoding="utf-8") as f:
        lines = [ln for ln in f.readlines() if ln.strip()]
    if limit is not None and limit > 0:
        lines = lines[-limit:]
    events: List[Dict[str, Any]] = []
    for line in lines:
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events


def save_infra_state(state: Dict[str, Any]) -> None:
    """Persist a materialized view of infra state to JSON.

    Higher layers are free to choose the exact shape of this dictionary.
    """

    INFRA_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with INFRA_STATE_PATH.open("w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, sort_keys=True)


def load_infra_state() -> Dict[str, Any]:
    """Load the last saved infra state snapshot, or return an empty dict."""

    if not INFRA_STATE_PATH.exists():
        return {}
    try:
        with INFRA_STATE_PATH.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}

