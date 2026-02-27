# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""layers/memory.py â€“ Memory / context-window usage layer."""

from __future__ import annotations
from .base import BaseLayer


class MemoryLayer(BaseLayer):
    name = "memory"

    def variables(self) -> list[str]:
        return ["memory.context_usage"]

    def collect(self) -> list[dict]:
        current = self._state.get_value("memory.context_usage", 0)
        return [self._make_record("memory.context_usage", current, units="tokens")]
