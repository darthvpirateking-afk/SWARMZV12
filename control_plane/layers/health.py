# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""layers/health.py â€“ System health layer."""

from __future__ import annotations
from .base import BaseLayer


class HealthLayer(BaseLayer):
    name = "health"

    def variables(self) -> list[str]:
        return ["health.system_health"]

    def collect(self) -> list[dict]:
        current = self._state.get_value("health.system_health", 100)
        return [self._make_record("health.system_health", current, units="percent")]
