# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""layers/swarm_health.py â€“ Swarm node availability layer."""

from __future__ import annotations
from .base import BaseLayer


class SwarmHealthLayer(BaseLayer):
    name = "swarm_health"

    def variables(self) -> list[str]:
        return ["swarm_health.node_availability"]

    def collect(self) -> list[dict]:
        current = self._state.get_value("swarm_health.node_availability", 100)
        return [self._make_record("swarm_health.node_availability", current,
                                  units="percent")]

