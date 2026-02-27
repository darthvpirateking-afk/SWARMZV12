# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
core/threshold.py — Threshold Layer (P0.4)

Unified activation engine consolidating all gate thresholds.
Deterministic trigger edges for XP, trials, ranks, QUARANTINE, budgets.

Pattern:
    result = threshold.check(metric, rule_name)
    if result.crossed:
        trigger_activation()

Architecture Role: Activation Layer
Doctrine: Threshold = Deterministic trigger edges, simplifies admit/deny
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, Optional, List

_CONFIG_DIR = Path(__file__).parent.parent / "config"
_THRESHOLDS_FILE = _CONFIG_DIR / "thresholds.json"


@dataclass
class LayerResult:
    """Deterministic state object returned by all layers."""

    layer: str
    passed: bool
    reason: str
    metadata: dict
    timestamp: float


@dataclass
class ThresholdCheck:
    """Result of threshold evaluation."""

    crossed: bool
    current: float
    limit: float
    rule_name: str
    reason: str


# Default threshold rules (loaded from config or these defaults)
DEFAULT_THRESHOLDS = {
    "quarantine": {
        "metric": "success_rate",
        "operator": "lt",
        "value": 0.30,
        "min_samples": 10,
        "description": "QUARANTINE triggered when success rate < 30% (10+ missions)",
    },
    "rank_e_to_d": {
        "metric": "missions_completed",
        "operator": "gte",
        "value": 1,
        "description": "Rank E → D after 1 mission",
    },
    "rank_d_to_c": {
        "metric": "missions_completed",
        "operator": "gte",
        "value": 10,
        "description": "Rank D → C after 10 missions",
    },
    "rank_c_to_b": {
        "metric": "missions_completed",
        "operator": "gte",
        "value": 50,
        "description": "Rank C → B after 50 missions",
    },
    "rank_b_to_a": {
        "metric": "missions_completed",
        "operator": "gte",
        "value": 100,
        "description": "Rank B → A after 100 missions",
    },
    "rank_a_to_s": {
        "metric": "missions_completed",
        "operator": "gte",
        "value": 200,
        "description": "Rank A → S after 200 missions",
    },
    "trial_required": {
        "metric": "trial_count",
        "operator": "eq",
        "value": 0,
        "description": "Trial gate check",
    },
    "budget_cap": {
        "metric": "budget_remaining",
        "operator": "gt",
        "value": 0,
        "description": "Budget must remain positive",
    },
    "rate_limit": {
        "metric": "requests_per_minute",
        "operator": "lte",
        "value": 120,
        "description": "Rate limit 120 req/min",
    },
}


class ThresholdLayer:
    """Unified activation engine for all thresholds."""

    def __init__(self, thresholds_path: Optional[Path] = None):
        self.thresholds_path = thresholds_path or _THRESHOLDS_FILE
        self.thresholds = self._load_thresholds()

    def _load_thresholds(self) -> Dict[str, Dict[str, Any]]:
        """Load threshold rules from config or use defaults."""
        if not self.thresholds_path.exists():
            _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            with open(self.thresholds_path, "w") as f:
                json.dump(DEFAULT_THRESHOLDS, f, indent=2)
            return DEFAULT_THRESHOLDS.copy()

        with open(self.thresholds_path, "r") as f:
            return json.load(f)

    def check_threshold(
        self,
        metric_value: float,
        rule_name: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> ThresholdCheck:
        """
        Check if metric crosses threshold.

        Args:
            metric_value: Current metric value
            rule_name: Name of threshold rule
            context: Additional context (e.g., min_samples check)

        Returns:
            ThresholdCheck with crossed status
        """
        context = context or {}

        if rule_name not in self.thresholds:
            return ThresholdCheck(
                crossed=False,
                current=metric_value,
                limit=0.0,
                rule_name=rule_name,
                reason=f"Unknown threshold rule: {rule_name}",
            )

        rule = self.thresholds[rule_name]
        limit = rule["value"]
        operator = rule["operator"]

        # Check min_samples requirement if present
        if "min_samples" in rule:
            sample_count = context.get("sample_count", 0)
            if sample_count < rule["min_samples"]:
                return ThresholdCheck(
                    crossed=False,
                    current=metric_value,
                    limit=limit,
                    rule_name=rule_name,
                    reason=f"Insufficient samples ({sample_count} < {rule['min_samples']})",
                )

        # Evaluate threshold
        crossed = self._evaluate_operator(metric_value, operator, limit)

        reason = rule.get("description", "")
        if crossed:
            reason = f"Threshold crossed: {metric_value} {operator} {limit}"
        else:
            reason = f"Below threshold: {metric_value} (limit: {limit})"

        return ThresholdCheck(
            crossed=crossed,
            current=metric_value,
            limit=limit,
            rule_name=rule_name,
            reason=reason,
        )

    def _evaluate_operator(self, value: float, operator: str, limit: float) -> bool:
        """Evaluate threshold operator."""
        ops = {
            "gt": lambda v, l: v > l,
            "gte": lambda v, l: v >= l,
            "lt": lambda v, l: v < l,
            "lte": lambda v, l: v <= l,
            "eq": lambda v, l: abs(v - l) < 1e-9,
            "neq": lambda v, l: abs(v - l) >= 1e-9,
        }
        return ops.get(operator, lambda v, l: False)(value, limit)

    def check_quarantine(
        self, success_rate: float, mission_count: int
    ) -> ThresholdCheck:
        """Convenience method for QUARANTINE check."""
        return self.check_threshold(
            success_rate,
            "quarantine",
            context={"sample_count": mission_count},
        )

    def check_rank_progression(
        self, missions_completed: int, current_rank: str
    ) -> Optional[str]:
        """
        Check if operator can progress to next rank.

        Returns next rank if threshold crossed, None otherwise.
        """
        rank_progression = {
            "E": ("rank_e_to_d", "D"),
            "D": ("rank_d_to_c", "C"),
            "C": ("rank_c_to_b", "B"),
            "B": ("rank_b_to_a", "A"),
            "A": ("rank_a_to_s", "S"),
        }

        if current_rank not in rank_progression:
            return None

        rule_name, next_rank = rank_progression[current_rank]
        result = self.check_threshold(missions_completed, rule_name)

        return next_rank if result.crossed else None

    def evaluate(self, action: Dict[str, Any], context: Dict[str, Any]) -> LayerResult:
        """
        Entry point for pipeline composition.

        Checks all relevant thresholds for the action.
        """
        # Extract metrics from action/context
        checks: List[ThresholdCheck] = []

        # Budget check: must have positive budget (crossed=True means budget > 0)
        if "budget_remaining" in context:
            budget_check = self.check_threshold(
                context["budget_remaining"],
                "budget_cap",
            )
            checks.append(budget_check)
            # FAIL if budget check NOT crossed (budget <= 0)
            if not budget_check.crossed:
                return LayerResult(
                    layer="threshold",
                    passed=False,
                    reason=f"Budget depleted: {context['budget_remaining']} remaining",
                    metadata={"check": "budget_cap", "checks": [budget_check.__dict__]},
                    timestamp=time.time(),
                )

        # Rate limit check: requests must be <= limit (crossed=False is good)
        if "requests_per_minute" in context:
            rate_check = self.check_threshold(
                context["requests_per_minute"],
                "rate_limit",
            )
            checks.append(rate_check)
            # FAIL if rate limit crossed (requests > limit)
            if not rate_check.crossed:
                return LayerResult(
                    layer="threshold",
                    passed=False,
                    reason=f"Rate limit exceeded: {context['requests_per_minute']} req/min",
                    metadata={"check": "rate_limit", "checks": [rate_check.__dict__]},
                    timestamp=time.time(),
                )

        # All threshold checks passed
        return LayerResult(
            layer="threshold",
            passed=True,
            reason="All threshold checks passed",
            metadata={
                "checks_performed": len(checks),
                "checks": [c.__dict__ for c in checks],
            },
            timestamp=time.time(),
        )


# Singleton instance
_threshold = ThresholdLayer()


def check_threshold(
    metric_value: float,
    rule_name: str,
    context: Optional[Dict[str, Any]] = None,
) -> ThresholdCheck:
    """Module-level convenience function."""
    return _threshold.check_threshold(metric_value, rule_name, context)


def check_quarantine(success_rate: float, mission_count: int) -> ThresholdCheck:
    """Module-level convenience function."""
    return _threshold.check_quarantine(success_rate, mission_count)


def check_rank_progression(missions_completed: int, current_rank: str) -> Optional[str]:
    """Module-level convenience function."""
    return _threshold.check_rank_progression(missions_completed, current_rank)


def evaluate(action: Dict[str, Any], context: Dict[str, Any]) -> LayerResult:
    """Module-level convenience function."""
    return _threshold.evaluate(action, context)
