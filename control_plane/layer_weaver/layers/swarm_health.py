"""
swarm_health.py – SwarmHealth layer: swarm infrastructure state variables.

Variables: task_latency_p95, error_rate, queue_depth, cost_per_day, agent_utilization
"""

from __future__ import annotations

from typing import List

from .base import BaseLayer


class SwarmHealthLayer(BaseLayer):

    name = "SwarmHealth"
    variables = ["task_latency_p95", "error_rate", "queue_depth",
                 "cost_per_day", "agent_utilization"]

    def __init__(self, defaults: dict | None = None):
        self._defaults = defaults or {
            "task_latency_p95": 2.1,
            "error_rate": 0.03,
            "queue_depth": 12,
            "cost_per_day": 8.5,
            "agent_utilization": 0.72,
        }

    def collect(self) -> List[dict]:
        return [
            self.make_record("SwarmHealth", "task_latency_p95",
                             self._defaults["task_latency_p95"],
                             "seconds", 0.9, "lower_better"),
            self.make_record("SwarmHealth", "error_rate",
                             self._defaults["error_rate"],
                             "ratio", 0.95, "lower_better"),
            self.make_record("SwarmHealth", "queue_depth",
                             self._defaults["queue_depth"],
                             "count", 0.9, "lower_better"),
            self.make_record("SwarmHealth", "cost_per_day",
                             self._defaults["cost_per_day"],
                             "USD", 0.85, "lower_better"),
            self.make_record("SwarmHealth", "agent_utilization",
                             self._defaults["agent_utilization"],
                             "ratio", 0.9, "higher_better"),
        ]
