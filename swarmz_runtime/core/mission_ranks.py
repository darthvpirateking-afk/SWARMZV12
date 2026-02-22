# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
Mission Ranks — SWARMZ V3.0 importance and threat classification for missions.

Ranks classify the priority/risk level of a mission from DELTA (routine)
through THRONE (sovereign directive).
"""

from __future__ import annotations

from typing import Any

MISSION_RANKS: list[dict[str, Any]] = [
    {
        "rank": "DELTA",
        "level": 1,
        "label": "Delta",
        "color": "#6c757d",
        "description": "Routine / low-impact operation",
    },
    {
        "rank": "CHARLIE",
        "level": 2,
        "label": "Charlie",
        "color": "#0d6efd",
        "description": "Standard operational mission",
    },
    {
        "rank": "BRAVO",
        "level": 3,
        "label": "Bravo",
        "color": "#fd7e14",
        "description": "Elevated priority or complexity",
    },
    {
        "rank": "ALPHA",
        "level": 4,
        "label": "Alpha",
        "color": "#dc3545",
        "description": "High-priority or high-risk mission",
    },
    {
        "rank": "THRONE",
        "level": 5,
        "label": "Throne",
        "color": "#6f42c1",
        "description": "Sovereign directive — operator-only",
    },
]

_RANK_INDEX: dict[str, dict[str, Any]] = {r["rank"]: r for r in MISSION_RANKS}


def list_ranks() -> list[dict[str, Any]]:
    return list(MISSION_RANKS)


def get_rank(rank_id: str) -> dict[str, Any] | None:
    return _RANK_INDEX.get(rank_id.upper())


def classify_mission(priority_score: float) -> dict[str, Any]:
    """Auto-classify a mission to a rank based on a 0–1 priority score."""
    if priority_score >= 0.9:
        return _RANK_INDEX["THRONE"]
    elif priority_score >= 0.7:
        return _RANK_INDEX["ALPHA"]
    elif priority_score >= 0.5:
        return _RANK_INDEX["BRAVO"]
    elif priority_score >= 0.3:
        return _RANK_INDEX["CHARLIE"]
    else:
        return _RANK_INDEX["DELTA"]
