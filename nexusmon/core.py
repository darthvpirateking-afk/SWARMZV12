"""nexusmon/core.py — NEXUSMON wakes up here.

Single source of truth for the entity state.  The FastAPI app lives in
swarmz_server; this module references it and exposes the live entity.

Import this to trigger entity boot tracking and to get the app reference:

    from nexusmon.core import app, entity
"""

from nexusmon.entity import get_entity

# ── Boot the entity ────────────────────────────────────────────────
# Called once on import.  Increments boot_count; on the very first boot
# prints "NEXUSMON is alive." via entity.boot().
entity = get_entity()

# ── Re-export the FastAPI app ──────────────────────────────────────
# The actual app instance lives in swarmz_server to preserve the
# existing route registration order.  We re-export it here so other
# nexusmon modules can reach it without creating circular imports.
from swarmz_server import app  # noqa: E402

__all__ = ["app", "entity"]
