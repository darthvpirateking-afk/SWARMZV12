# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""App Store rankings proxy — returns simulated live ranking data."""

import random
import time
from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import APIRouter

router = APIRouter()

# ── Seed data ─────────────────────────────────────────────────────────────────

_APPS: List[Dict[str, Any]] = [
    {"id": "com.supercell.clashroyale", "name": "Clash Royale", "category": "Games", "developer": "Supercell"},
    {"id": "com.tiktok.app", "name": "TikTok", "category": "Entertainment", "developer": "TikTok"},
    {"id": "com.spotify.music", "name": "Spotify", "category": "Music", "developer": "Spotify"},
    {"id": "com.discord.app", "name": "Discord", "category": "Social", "developer": "Discord"},
    {"id": "com.netflix.app", "name": "Netflix", "category": "Entertainment", "developer": "Netflix"},
    {"id": "com.instagram.app", "name": "Instagram", "category": "Social", "developer": "Meta"},
    {"id": "com.youtube.app", "name": "YouTube", "category": "Entertainment", "developer": "Google"},
    {"id": "com.snapchat.app", "name": "Snapchat", "category": "Social", "developer": "Snap"},
    {"id": "com.roblox.robloxmobile", "name": "Roblox", "category": "Games", "developer": "Roblox"},
    {"id": "com.duolingo.app", "name": "Duolingo", "category": "Education", "developer": "Duolingo"},
    {"id": "com.amazon.app", "name": "Amazon", "category": "Shopping", "developer": "Amazon"},
    {"id": "com.uber.driver", "name": "Uber", "category": "Travel", "developer": "Uber"},
    {"id": "com.google.maps", "name": "Google Maps", "category": "Navigation", "developer": "Google"},
    {"id": "com.zoom.app", "name": "Zoom", "category": "Business", "developer": "Zoom"},
    {"id": "com.shazam.app", "name": "Shazam", "category": "Music", "developer": "Apple"},
]

# Stable pseudo-random ratings per app
_RATINGS = {app["id"]: round(3.5 + random.Random(app["id"]).random() * 1.5, 1) for app in _APPS}
_REVIEWS = {app["id"]: random.Random(app["id"] + "r").randint(50_000, 5_000_000) for app in _APPS}

# ── Ranking simulation ────────────────────────────────────────────────────────

_SEED_OFFSET = int(time.time() // 300)  # rotate every 5 minutes


def _generate_rankings(category: str | None = None) -> List[Dict[str, Any]]:
    """Return a ranked list that slowly shifts over time."""
    bucket = int(time.time() // 300)  # changes every 5 min
    apps = [a for a in _APPS if category is None or a["category"].lower() == category.lower()]
    rng = random.Random(bucket)

    # Assign a score per app that changes each bucket but stays plausible
    scored = []
    for i, app in enumerate(apps):
        base_score = len(apps) - i  # natural starting order
        jitter = rng.randint(-2, 2)
        scored.append((max(1, base_score + jitter), app))

    scored.sort(key=lambda x: -x[0])

    # Compute previous bucket ranking for delta
    prev_rng = random.Random(bucket - 1)
    prev_scored = []
    for i, app in enumerate(apps):
        base_score = len(apps) - i
        jitter = prev_rng.randint(-2, 2)
        prev_scored.append((max(1, base_score + jitter), app))
    prev_scored.sort(key=lambda x: -x[0])
    prev_rank = {app["id"]: rank + 1 for rank, (_, app) in enumerate(prev_scored)}

    result = []
    for rank, (_, app) in enumerate(scored, start=1):
        prev = prev_rank.get(app["id"], rank)
        delta = prev - rank  # positive = moved up
        result.append(
            {
                "rank": rank,
                "previous_rank": prev,
                "delta": delta,
                "id": app["id"],
                "name": app["name"],
                "category": app["category"],
                "developer": app["developer"],
                "rating": _RATINGS[app["id"]],
                "reviews": _REVIEWS[app["id"]],
            }
        )
    return result


@router.get("/rankings")
def get_rankings(category: str | None = None, limit: int = 15) -> Dict[str, Any]:
    """Return simulated App Store rankings with live deltas."""
    rankings = _generate_rankings(category)[:limit]
    return {
        "rankings": rankings,
        "total": len(rankings),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "category": category or "all",
        "next_update_in": 300 - (int(time.time()) % 300),
    }


@router.get("/categories")
def get_categories() -> Dict[str, Any]:
    """Return available categories."""
    cats = sorted({app["category"] for app in _APPS})
    return {"categories": cats}
