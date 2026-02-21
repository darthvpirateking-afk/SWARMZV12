"""
health.py – Health layer: personal health state variables.

Variables: sleep_hours_avg, fatigue_score, resting_hr
"""

from __future__ import annotations

from typing import List

from .base import BaseLayer


class HealthLayer(BaseLayer):

    name = "Health"
    variables = ["sleep_hours_avg", "fatigue_score", "resting_hr"]

    def __init__(self, defaults: dict | None = None):
        self._defaults = defaults or {
            "sleep_hours_avg": 6.5,
            "fatigue_score": 55,
            "resting_hr": 68,
        }

    def collect(self) -> List[dict]:
        return [
            self.make_record(
                "Health",
                "sleep_hours_avg",
                self._defaults["sleep_hours_avg"],
                "hours",
                0.9,
                "higher_better",
            ),
            self.make_record(
                "Health",
                "fatigue_score",
                self._defaults["fatigue_score"],
                "score_0_100",
                0.85,
                "lower_better",
            ),
            self.make_record(
                "Health",
                "resting_hr",
                self._defaults["resting_hr"],
                "bpm",
                0.9,
                "lower_better",
            ),
        ]
