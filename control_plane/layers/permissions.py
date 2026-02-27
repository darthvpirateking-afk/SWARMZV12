# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""layers/permissions.py â€“ Access-scope / permissions layer."""

from __future__ import annotations
from .base import BaseLayer


class PermissionsLayer(BaseLayer):
    name = "permissions"

    def variables(self) -> list[str]:
        return ["permissions.access_scope"]

    def collect(self) -> list[dict]:
        current = self._state.get_value("permissions.access_scope", 50)
        return [
            self._make_record("permissions.access_scope", current, units="scope_units")
        ]
