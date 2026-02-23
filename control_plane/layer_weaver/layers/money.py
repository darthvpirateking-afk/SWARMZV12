"""
money.py – Money layer: financial state variables.

Variables: burn_weekly_usd, runway_weeks, discretionary_spend_usd, revenue_weekly_usd
"""

from __future__ import annotations

from typing import List

from .base import BaseLayer


class MoneyLayer(BaseLayer):
    name = "Money"
    variables = [
        "burn_weekly_usd",
        "runway_weeks",
        "discretionary_spend_usd",
        "revenue_weekly_usd",
    ]

    def __init__(self, defaults: dict | None = None):
        self._defaults = defaults or {
            "burn_weekly_usd": 2500,
            "runway_weeks": 18,
            "discretionary_spend_usd": 400,
            "revenue_weekly_usd": 1800,
        }

    def collect(self) -> List[dict]:
        return [
            self.make_record(
                "Money",
                "burn_weekly_usd",
                self._defaults["burn_weekly_usd"],
                "USD",
                0.95,
                "lower_better",
            ),
            self.make_record(
                "Money",
                "runway_weeks",
                self._defaults["runway_weeks"],
                "weeks",
                0.9,
                "higher_better",
            ),
            self.make_record(
                "Money",
                "discretionary_spend_usd",
                self._defaults["discretionary_spend_usd"],
                "USD",
                0.85,
                "neutral",
            ),
            self.make_record(
                "Money",
                "revenue_weekly_usd",
                self._defaults["revenue_weekly_usd"],
                "USD",
                0.8,
                "higher_better",
            ),
        ]
