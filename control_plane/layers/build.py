# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""layers/build.py â€“ CI / build pass-rate layer."""

from __future__ import annotations
from .base import BaseLayer


class BuildLayer(BaseLayer):
    name = "build"

    def variables(self) -> list[str]:
        return ["build.pass_rate"]

    def collect(self) -> list[dict]:
        current = self._state.get_value("build.pass_rate", 100)
        return [self._make_record("build.pass_rate", current, units="percent")]

