# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
Swarm Tiers — SWARMZ V3.0 capability classification for swarm agents.

Tiers gate what operations an agent can perform based on mission count.
"""

from __future__ import annotations

from typing import Any

SWARM_TIERS: list[dict[str, Any]] = [
    {
        "tier": 0,
        "id": "RECRUIT",
        "label": "Recruit",
        "capabilities": ["observe"],
        "min_missions": 0,
    },
    {
        "tier": 1,
        "id": "SCOUT",
        "label": "Scout",
        "capabilities": ["observe", "report"],
        "min_missions": 5,
    },
    {
        "tier": 2,
        "id": "OPERATIVE",
        "label": "Operative",
        "capabilities": ["observe", "report", "execute"],
        "min_missions": 25,
    },
    {
        "tier": 3,
        "id": "GUARDIAN",
        "label": "Guardian",
        "capabilities": ["observe", "report", "execute", "defend"],
        "min_missions": 75,
    },
    {
        "tier": 4,
        "id": "COMMANDER",
        "label": "Commander",
        "capabilities": ["observe", "report", "execute", "defend", "command"],
        "min_missions": 200,
    },
    {
        "tier": 5,
        "id": "SOVEREIGN",
        "label": "Sovereign",
        "capabilities": ["all"],
        "min_missions": 500,
    },
]

_TIER_INDEX: dict[str, dict[str, Any]] = {t["id"]: t for t in SWARM_TIERS}


def list_tiers() -> list[dict[str, Any]]:
    return list(SWARM_TIERS)


def get_tier(tier_id: str) -> dict[str, Any] | None:
    return _TIER_INDEX.get(tier_id.upper())


def resolve_tier_for_missions(mission_count: int) -> dict[str, Any]:
    """Return the highest tier an agent qualifies for given their mission count."""
    qualified = [t for t in SWARM_TIERS if mission_count >= t["min_missions"]]
    return qualified[-1] if qualified else SWARM_TIERS[0]
