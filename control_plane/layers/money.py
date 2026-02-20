# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""layers/money.py â€“ Budget / financial layer."""

from __future__ import annotations
from .base import BaseLayer


class MoneyLayer(BaseLayer):
    name = "money"

    def variables(self) -> list[str]:
        return ["money.budget_remaining"]

    def collect(self) -> list[dict]:
        current = self._state.get_value("money.budget_remaining", 1000)
        return [self._make_record("money.budget_remaining", current, units="USD")]

