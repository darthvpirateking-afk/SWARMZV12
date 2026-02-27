#!/usr/bin/env python3
"""
Timeline Store — Append-only event log for organism evolution.
Tracks: plugin installs/unlocks, XP gains, rank ups, missions, evolution events.
"""

import json
import uuid
import os
from datetime import datetime
from typing import Dict, List, Any, Optional

TIMELINE_PATH = "data/timeline.json"


def ensure_dir():
    """Create data directory if missing."""
    os.makedirs("data", exist_ok=True)


def load_timeline() -> List[Dict[str, Any]]:
    """Load all timeline events from disk."""
    ensure_dir()
    try:
        with open(TIMELINE_PATH, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def append_event(
    event_type: str, payload: Dict[str, Any], plugin_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Append a new timeline event.

    Args:
        event_type: plugin_installed, plugin_unlocked, xp_gain, rank_up, mission_complete, evolution, system
        payload: event-specific data
        plugin_id: optional plugin context

    Returns:
        The appended event record.
    """
    ensure_dir()
    timeline = load_timeline()

    evt = {
        "id": str(uuid.uuid4()),
        "type": event_type,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "payload": payload,
    }

    if plugin_id:
        evt["plugin_id"] = plugin_id

    timeline.append(evt)

    with open(TIMELINE_PATH, "w") as f:
        json.dump(timeline, f, indent=2)

    return evt


def get_timeline_slice(
    limit: int = 100, offset: int = 0, event_type: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Retrieve a slice of timeline (for pagination + filtering).

    Args:
        limit: max events to return
        offset: skip this many events
        event_type: filter by type (optional)

    Returns:
        List of timeline events (most recent first).
    """
    timeline = load_timeline()

    if event_type:
        timeline = [e for e in timeline if e.get("type") == event_type]

    # Most recent first
    timeline.reverse()

    return timeline[offset : offset + limit]


def get_stats() -> Dict[str, Any]:
    """
    Quick stats about the timeline (for cockpit dashboard).

    Returns:
        {
            "total_events": int,
            "plugins_installed": int,
            "plugins_unlocked": int,
            "rank_ups": int,
            "missions_completed": int,
            "evolutions": int
        }
    """
    timeline = load_timeline()

    stats = {
        "total_events": len(timeline),
        "plugins_installed": len(
            [e for e in timeline if e.get("type") == "plugin_installed"]
        ),
        "plugins_unlocked": len(
            [e for e in timeline if e.get("type") == "plugin_unlocked"]
        ),
        "rank_ups": len([e for e in timeline if e.get("type") == "rank_up"]),
        "missions_completed": len(
            [e for e in timeline if e.get("type") == "mission_complete"]
        ),
        "evolutions": len([e for e in timeline if e.get("type") == "evolution"]),
    }

    return stats
