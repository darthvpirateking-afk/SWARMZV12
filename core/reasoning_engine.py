"""Lightweight reasoning core selector for NEXUSMON.

This module intentionally keeps a small surface area because the router only
requires core switching and active-core reporting.
"""

from dataclasses import dataclass


@dataclass
class ReasoningEngine:
	"""Holds and switches the active reasoning core."""

	active_core: str = "default"

	def switch_core(self, core_name: str) -> str:
		"""Switch the active reasoning core name.

		Falls back to ``default`` when no valid name is provided.
		"""
		normalized = (core_name or "").strip()
		self.active_core = normalized or "default"
		return self.active_core


reasoning_engine = ReasoningEngine()

