"""
permissions.py – Permissions layer (minimal stub).

Conforms to the BaseLayer interface for future expansion.
"""

from __future__ import annotations

from typing import List

from .base import BaseLayer


class PermissionsLayer(BaseLayer):
    name = "Permissions"
    variables = ["access_scope"]

    def collect(self) -> List[dict]:
        return [
            self.make_record(
                "Permissions", "access_scope", 1.0, "level", 0.95, "neutral"
            ),
        ]
