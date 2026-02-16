"""
memory.py – Memory layer (minimal stub).

Conforms to the BaseLayer interface for future expansion.
"""

from __future__ import annotations

from typing import List

from .base import BaseLayer


class MemoryLayer(BaseLayer):

    name = "Memory"
    variables = ["memory_utilization"]

    def collect(self) -> List[dict]:
        return [
            self.make_record("Memory", "memory_utilization", 0.45,
                             "ratio", 0.9, "lower_better"),
        ]
