from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def generate_mission_changelog(mission_id: str, events: list[dict[str, Any]]) -> dict[str, Any]:
    ordered = sorted(events, key=lambda item: item.get("timestamp", ""))
    changes: list[str] = []

    for event in ordered:
        label = event.get("event") or event.get("type") or "unknown_event"
        detail = event.get("detail") or event.get("message") or ""
        if detail:
            changes.append(f"{label}: {detail}")
        else:
            changes.append(label)

    return {
        "mission_id": mission_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "change_count": len(changes),
        "changes": changes,
    }


def generate_release_notes(mission_id: str, findings: list[dict[str, Any]]) -> dict[str, Any]:
    critical = [item for item in findings if str(item.get("severity", "")).lower() == "critical"]
    high = [item for item in findings if str(item.get("severity", "")).lower() == "high"]

    highlights = []
    if critical:
        highlights.append(f"{len(critical)} critical finding(s) identified.")
    if high:
        highlights.append(f"{len(high)} high finding(s) identified.")
    if not highlights:
        highlights.append("No critical/high findings in this mission.")

    return {
        "mission_id": mission_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "highlights": highlights,
    }
