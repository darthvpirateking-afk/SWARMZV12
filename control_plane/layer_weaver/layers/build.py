"""
build.py – Build layer: development/shipping state variables.

Variables: shipped_artifacts_weekly, deep_work_hours_weekly,
           cycle_time_days, bug_regressions_weekly, wip_limit
"""

from __future__ import annotations

from typing import List

from .base import BaseLayer


class BuildLayer(BaseLayer):
    name = "Build"
    variables = [
        "shipped_artifacts_weekly",
        "deep_work_hours_weekly",
        "cycle_time_days",
        "bug_regressions_weekly",
        "wip_limit",
    ]

    def __init__(self, defaults: dict | None = None):
        self._defaults = defaults or {
            "shipped_artifacts_weekly": 3,
            "deep_work_hours_weekly": 12,
            "cycle_time_days": 5,
            "bug_regressions_weekly": 2,
            "wip_limit": 5,
        }

    def collect(self) -> List[dict]:
        return [
            self.make_record(
                "Build",
                "shipped_artifacts_weekly",
                self._defaults["shipped_artifacts_weekly"],
                "count",
                0.95,
                "higher_better",
            ),
            self.make_record(
                "Build",
                "deep_work_hours_weekly",
                self._defaults["deep_work_hours_weekly"],
                "hours",
                0.85,
                "higher_better",
            ),
            self.make_record(
                "Build",
                "cycle_time_days",
                self._defaults["cycle_time_days"],
                "days",
                0.8,
                "lower_better",
            ),
            self.make_record(
                "Build",
                "bug_regressions_weekly",
                self._defaults["bug_regressions_weekly"],
                "count",
                0.9,
                "lower_better",
            ),
            self.make_record(
                "Build",
                "wip_limit",
                self._defaults["wip_limit"],
                "count",
                0.95,
                "lower_better",
            ),
        ]
