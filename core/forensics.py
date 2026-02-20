# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
SWARMZ Forensics Module â€” post-run investigation utilities.

Read-only analysis over:
- data/missions.jsonl
- data/audit.jsonl
- packs/<mission_id>/*

Outputs deterministic "case files" describing what happened, what
changed, and which preceding actions likely contributed â€” based only on
local evidence. No runtime behaviour is changed.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from jsonl_utils import read_jsonl
from core.atomic import atomic_append_jsonl

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
MISSIONS_FILE = DATA_DIR / "missions.jsonl"
AUDIT_FILE = DATA_DIR / "audit.jsonl"
PACKS_DIR = ROOT / "packs"
FORENSICS_LOG = DATA_DIR / "audit_forensics.jsonl"


FORENSICS_CONFIG: Dict[str, Any] = {
    "timeline_tail": 200,
}


@dataclass
class TimelineEvent:
    timestamp: str
    event: str
    mission_id: str
    payload: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        # Ensure stable key order
        return {
            "timestamp": d["timestamp"],
            "event": d["event"],
            "mission_id": d["mission_id"],
            "payload": d["payload"],
        }


@dataclass
class CaseFile:
    mission_id: str
    goal: Optional[str]
    category: Optional[str]
    status: Optional[str]
    created_at: Optional[str]
    timeline: List[Dict[str, Any]]
    what_happened: str
    what_changed: List[str]
    preceding_actions: List[str]
    contributing_factors: List[str]
    artifacts: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# â”€â”€ Internal loaders (read-only) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def _load_missions() -> List[Dict[str, Any]]:
    rows, _, _ = read_jsonl(MISSIONS_FILE)
    return rows


def _load_audit() -> List[Dict[str, Any]]:
    rows, _, _ = read_jsonl(AUDIT_FILE)
    return rows


def _find_mission(mission_id: str) -> Optional[Dict[str, Any]]:
    for m in _load_missions():
        if str(m.get("mission_id")) == mission_id:
            return m
    return None


def _load_artifacts(mission_id: str) -> Dict[str, Any]:
    base = PACKS_DIR / mission_id
    if not base.exists() or not base.is_dir():
        return {"pack_path": None, "files": []}

    files: List[str] = []
    for p in sorted(base.rglob("*")):
        if p.is_file():
            files.append(str(p.relative_to(ROOT)))
    return {"pack_path": str(base.relative_to(ROOT)), "files": files}


# â”€â”€ Timeline reconstruction â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def build_timeline(mission_id: str) -> List[Dict[str, Any]]:
    """Build a chronological timeline of events for a mission."""
    mission = _find_mission(mission_id)
    audit_rows = [r for r in _load_audit() if str(r.get("mission_id")) == mission_id]

    out: List[TimelineEvent] = []

    if mission:
        created_at = mission.get("created_at") or mission.get("timestamp")
        out.append(TimelineEvent(
            timestamp=created_at or "",
            event="mission_created",
            mission_id=mission_id,
            payload={
                "goal": mission.get("goal"),
                "category": mission.get("category"),
                "status": mission.get("status"),
            },
        ))

    for row in audit_rows:
        ts = str(row.get("timestamp") or "")
        ev = str(row.get("event") or row.get("event_type") or "audit_event")
        payload = {k: v for k, v in row.items() if k not in ("timestamp", "event", "event_type")}
        out.append(TimelineEvent(timestamp=ts, event=ev, mission_id=mission_id, payload=payload))

    # Sort by timestamp with a stable fallback to original order
    out.sort(key=lambda e: e.timestamp or "")

    # Trim to the most recent tail, if configured
    tail = int(FORENSICS_CONFIG.get("timeline_tail", 0) or 0)
    if tail and len(out) > tail:
        out = out[-tail:]

    return [e.to_dict() for e in out]


# â”€â”€ Case file synthesis (deterministic) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def _summarize_what_happened(mission: Optional[Dict[str, Any]], timeline: List[Dict[str, Any]]) -> str:
    if not mission:
        return "Mission not found in missions.jsonl."

    status = (mission.get("status") or "UNKNOWN").upper()
    goal = mission.get("goal") or "(no goal)"
    category = mission.get("category") or "(no category)"

    last_ts = timeline[-1]["timestamp"] if timeline else mission.get("created_at") or "(unknown)"
    return (
        f"Mission {mission.get('mission_id')} in category '{category}' "
        f"was created to pursue goal '{goal}'. Final status: {status}. "
        f"Last recorded activity at {last_ts}."
    )


def _summarize_changes(timeline: List[Dict[str, Any]]) -> List[str]:
    changes: List[str] = []
    for ev in timeline:
        name = ev.get("event", "")
        if name in {"mission_created", "mission_run", "mission_completed", "mission_failed"}:
            changes.append(f"Event: {name} at {ev.get('timestamp')}")
    return changes


def _summarize_preceding_actions(timeline: List[Dict[str, Any]]) -> List[str]:
    """Return a stable, human-readable list of preceding actions."""
    preceding: List[str] = []
    for ev in timeline:
        name = str(ev.get("event") or "")
        if name.startswith("trial_"):
            preceding.append(f"Trial event: {name}")
        if name.endswith("_dispatched") or name.endswith("_created"):
            preceding.append(f"Dispatch: {name}")
    # De-duplicate while preserving order
    seen = set()
    uniq: List[str] = []
    for s in preceding:
        if s in seen:
            continue
        seen.add(s)
        uniq.append(s)
    return uniq


def _summarize_contributing_factors(mission: Optional[Dict[str, Any]], timeline: List[Dict[str, Any]]) -> List[str]:
    factors: List[str] = []
    if not mission:
        return factors

    status = (mission.get("status") or "").upper()
    if status == "SUCCESS":
        factors.append("Outcome: SUCCESS â€” preceding actions likely sufficient.")
    elif status == "FAILURE":
        factors.append("Outcome: FAILURE â€” inspect trials, errors, and rollbacks.")
    elif status == "RUNNING":
        factors.append("Outcome: RUNNING â€” investigation should focus on stuck states.")

    # Basic heuristic: count error-like audit events
    error_like = [ev for ev in timeline if "error" in str(ev.get("event", "")).lower()]
    if error_like:
        factors.append(f"Detected {len(error_like)} error-like events in timeline.")

    return factors


def build_casefile(mission_id: str) -> Optional[Dict[str, Any]]:
    mission = _find_mission(mission_id)
    if not mission:
        return None

    timeline = build_timeline(mission_id)
    what_happened = _summarize_what_happened(mission, timeline)
    what_changed = _summarize_changes(timeline)
    preceding_actions = _summarize_preceding_actions(timeline)
    contributing_factors = _summarize_contributing_factors(mission, timeline)
    artifacts = _load_artifacts(mission_id)

    cf = CaseFile(
        mission_id=mission_id,
        goal=mission.get("goal"),
        category=mission.get("category"),
        status=mission.get("status"),
        created_at=mission.get("created_at"),
        timeline=timeline,
        what_happened=what_happened,
        what_changed=what_changed,
        preceding_actions=preceding_actions,
        contributing_factors=contributing_factors,
        artifacts=artifacts,
    )
    return cf.to_dict()


# â”€â”€ Self-check / audit helpers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def _audit(event: str, payload: Dict[str, Any]) -> None:
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": event,
        "payload": payload,
    }
    atomic_append_jsonl(FORENSICS_LOG, entry)


def self_check() -> Dict[str, Any]:
    """Lightweight self-check for wiring + schema.

    If no missions exist yet, this still returns ok=True with a
    placeholder payload. No runtime data is mutated.
    """
    missions = _load_missions()
    first = missions[0] if missions else None

    if first:
        mid = str(first.get("mission_id"))
        casefile = build_casefile(mid)
        payload = {"sample_mission_id": mid, "has_casefile": casefile is not None}
    else:
        payload = {"sample_mission_id": None, "has_casefile": False}

    _audit("forensics_self_check", payload)
    return {"ok": True, **payload}

