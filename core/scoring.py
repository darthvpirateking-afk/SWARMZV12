# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
core/scoring.py — Pre-evaluated Scoring Layer (P0.3)

Multi-factor scoring for deterministic action admission control.
Every risky action scored before execution.

Pattern:
    score_result = scoring.score(action)
    if score_result.risk > threshold:
        deny(score_result.reason)

Architecture Role: Scoring Layer
Doctrine: Pre-evaluated = Converts uncertainty into scored decisions
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class LayerResult:
    """Deterministic state object returned by all layers."""
    layer: str
    passed: bool
    reason: str
    metadata: dict
    timestamp: float


@dataclass
class ActionScore:
    """Multi-factor action score."""
    risk: float  # 0-100 scale
    cost: float  # resource cost estimate
    reversibility: bool
    complexity: int  # 1-10 scale
    operator_confidence: float  # 0-1 based on history
    reason: str


class ScoringLayer:
    """Pre-evaluated scoring engine for action admission."""

    def __init__(self):
        # Risk weights for different action types
        self.risk_weights = {
            "shell_command": 80.0,
            "api_call": 60.0,
            "file_write": 40.0,
            "file_delete": 90.0,
            "purchase": 95.0,
            "message": 20.0,
            "schedule": 10.0,
            "read": 5.0,
        }
        
        # Rank-based risk multipliers (from nexusmon_mission_engine)
        self.rank_multipliers = {
            "S": 5.0,
            "A": 4.0,
            "B": 2.5,
            "C": 1.5,
            "D": 1.0,
            "E": 0.5,
        }

    def calculate_risk(self, action: Dict[str, Any]) -> float:
        """
        Calculate 0-100 risk score.
        
        Factors:
        - Action type base risk
        - Mission rank multiplier
        - Reversibility modifier
        - Dependencies complexity
        """
        action_type = action.get("type", "unknown").lower()
        base_risk = self.risk_weights.get(action_type, 50.0)
        
        # Rank multiplier
        rank = action.get("rank", "E").upper()
        rank_mult = self.rank_multipliers.get(rank, 1.0)
        
        # Reversibility modifier (reduce risk if rollback available)
        reversibility = action.get("reversibility", False)
        reversibility_modifier = 0.7 if reversibility else 1.0
        
        # Dependencies complexity (more deps = higher risk)
        dependencies = action.get("dependencies", [])
        dep_modifier = min(1.0 + (len(dependencies) * 0.1), 2.0)
        
        risk = base_risk * rank_mult * reversibility_modifier * dep_modifier
        return min(risk, 100.0)  # Cap at 100

    def calculate_cost(self, action: Dict[str, Any]) -> float:
        """
        Estimate resource cost.
        
        Based on:
        - Execution time estimate
        - API call count
        - Storage requirements
        """
        # Simple cost model (can be enhanced)
        base_cost = 1.0
        
        # Execution time factor
        estimated_seconds = action.get("estimated_seconds", 10)
        time_cost = estimated_seconds / 60.0  # Normalize to minutes
        
        # API call cost
        api_calls = action.get("api_calls", 0)
        api_cost = api_calls * 0.1
        
        # Storage cost
        storage_mb = action.get("storage_mb", 0)
        storage_cost = storage_mb * 0.01
        
        return base_cost + time_cost + api_cost + storage_cost

    def calculate_complexity(self, action: Dict[str, Any]) -> int:
        """
        Calculate 1-10 complexity score.
        
        Based on:
        - Number of steps
        - Dependencies count
        - Conditional branches
        """
        steps = action.get("steps", 1)
        dependencies = len(action.get("dependencies", []))
        branches = action.get("branches", 0)
        
        complexity = min(steps + dependencies + branches, 10)
        return max(complexity, 1)

    def calculate_operator_confidence(
        self,
        action: Dict[str, Any],
        context: Dict[str, Any],
    ) -> float:
        """
        Calculate 0-1 operator confidence based on history.
        
        Uses:
        - Success rate for similar actions
        - Operator rank/level
        - Trial completions
        """
        # Get operator stats from context
        success_rate = context.get("operator_success_rate", 0.5)
        operator_rank = context.get("operator_rank", "E")
        trials_completed = context.get("trials_completed", 0)
        
        # Base confidence from success rate
        confidence = success_rate
        
        # Rank bonus (higher ranks = more confidence)
        rank_bonus = {"S": 0.3, "A": 0.2, "B": 0.1, "C": 0.05}.get(operator_rank, 0.0)
        confidence += rank_bonus
        
        # Trial experience bonus
        trial_bonus = min(trials_completed * 0.01, 0.2)
        confidence += trial_bonus
        
        return min(confidence, 1.0)

    def score(
        self,
        action: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> ActionScore:
        """
        Generate multi-factor score for action.
        
        Returns ActionScore with all dimensions.
        """
        context = context or {}
        
        risk = self.calculate_risk(action)
        cost = self.calculate_cost(action)
        reversibility = action.get("reversibility", False)
        complexity = self.calculate_complexity(action)
        operator_confidence = self.calculate_operator_confidence(action, context)
        
        # Generate reason string
        if risk > 80:
            reason = f"High-risk action (score: {risk:.1f})"
        elif risk > 50:
            reason = f"Medium-risk action (score: {risk:.1f})"
        else:
            reason = f"Low-risk action (score: {risk:.1f})"
        
        if not reversibility:
            reason += " [non-reversible]"
        
        return ActionScore(
            risk=risk,
            cost=cost,
            reversibility=reversibility,
            complexity=complexity,
            operator_confidence=operator_confidence,
            reason=reason,
        )

    def evaluate(
        self,
        action: Dict[str, Any],
        context: Dict[str, Any],
        risk_threshold: float = 80.0,
    ) -> LayerResult:
        """
        Entry point for pipeline composition.
        
        Returns LayerResult with pass/fail based on risk threshold.
        """
        score = self.score(action, context)
        
        # Admission decision based on risk threshold
        passed = score.risk <= risk_threshold
        
        return LayerResult(
            layer="scoring",
            passed=passed,
            reason=score.reason if passed else f"Risk score {score.risk:.1f} exceeds threshold {risk_threshold}",
            metadata={
                "risk": score.risk,
                "cost": score.cost,
                "reversibility": score.reversibility,
                "complexity": score.complexity,
                "operator_confidence": score.operator_confidence,
                "threshold": risk_threshold,
            },
            timestamp=time.time(),
        )


# Singleton instance
_scoring = ScoringLayer()


def score(action: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> ActionScore:
    """Module-level convenience function."""
    return _scoring.score(action, context)


def evaluate(
    action: Dict[str, Any],
    context: Dict[str, Any],
    risk_threshold: float = 80.0,
) -> LayerResult:
    """Module-level convenience function."""
    return _scoring.evaluate(action, context, risk_threshold)
