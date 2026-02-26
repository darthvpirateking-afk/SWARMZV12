"""
Exploration Layer (P2.4 - Safe Experimentation)

Manages safe exploration of new behaviors and strategies.
Defines exploration boundaries and fallback mechanisms.

Design:
- Controlled randomness within safety bounds
- Exploration vs exploitation balance
- Safe failure zones
- Automatic reversion on exploration failure
"""

import time
import random
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum

from core.reversible import LayerResult


class ExplorationMode(str, Enum):
    """Exploration strategy modes."""
    EXPLOIT = "exploit"      # Use known-good strategies only
    EXPLORE = "explore"      # Try new approaches
    BALANCED = "balanced"    # Mix of both
    ADAPTIVE = "adaptive"    # Adjust based on success


@dataclass
class ExplorationBound:
    """Safety boundary for exploration."""
    parameter: str
    safe_min: float
    safe_max: float
    fallback_value: float


@dataclass
class ExplorationResult:
    """Result of an exploration attempt."""
    timestamp: float
    strategy: str
    success: bool
    reward: float  # Outcome metric
    reverted: bool = False


class ExplorationLayer:
    """
    Safe experimentation engine.
    
    Manages exploration/exploitation tradeoff with safety constraints.
    """
    
    def __init__(self, seed: Optional[int] = None):
        self.mode = ExplorationMode.BALANCED
        self.exploration_rate = 0.1  # 10% explore, 90% exploit
        self.bounds: Dict[str, ExplorationBound] = {}
        self.exploration_history: List[ExplorationResult] = []
        self.known_good_strategies: List[str] = []
        
        # Deterministic RNG for reproducibility
        if seed is not None:
            random.seed(seed)
        
        self._load_default_bounds()
    
    def _load_default_bounds(self):
        """Initialize with safety bounds."""
        self.add_bound(ExplorationBound(
            parameter="risk_score",
            safe_min=0.0,
            safe_max =70.0,  # Don't explore above 70 risk
            fallback_value=30.0,
        ))
        
        self.add_bound(ExplorationBound(
            parameter="complexity",
            safe_min=1.0,
            safe_max=5.0,  # Limit complexity in exploration
            fallback_value=2.0,
        ))
    
    def add_bound(self, bound: ExplorationBound):
        """Add an exploration safety bound."""
        self.bounds[bound.parameter] = bound
    
    def is_safe_to_explore(self, context: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Check if current state is safe for exploration.
        
        Returns (is_safe, reason_if_unsafe).
        """
        for param, bound in self.bounds.items():
            value = context.get(param)
            
            if value is not None and isinstance(value, (int, float)):
                if value < bound.safe_min or value > bound.safe_max:
                    return False, f"{param} = {value} outside safe bounds [{bound.safe_min}, {bound.safe_max}]"
        
        return True, None
    
    def should_explore(self) -> bool:
        """Decide whether to explore or exploit."""
        if self.mode == ExplorationMode.EXPLOIT:
            return False
        elif self.mode == ExplorationMode.EXPLORE:
            return True
        elif self.mode == ExplorationMode.BALANCED:
            return random.random() < self.exploration_rate
        else:  # ADAPTIVE
            # Increase exploration if recent success rate is high
            if len(self.exploration_history) < 10:
                return random.random() < 0.2  # Conservative initially
            
            recent = self.exploration_history[-10:]
            success_rate = sum(1 for r in recent if r.success) / len(recent)
            
            # Higher success = more exploration
            adaptive_rate = min(0.3, success_rate * 0.4)
            return random.random() < adaptive_rate
    
    def clamp_to_bounds(self, parameters: Dict[str, float]) -> Dict[str, float]:
        """Clamp parameters to safety bounds."""
        clamped = parameters.copy()
        
        for param, value in parameters.items():
            if param in self.bounds:
                bound = self.bounds[param]
                clamped[param] = max(bound.safe_min, min(bound.safe_max, value))
        
        return clamped
    
    def record_exploration(self, strategy: str, success: bool, reward: float, reverted: bool = False):
        """Record an exploration attempt."""
        result = ExplorationResult(
            timestamp=time.time(),
            strategy=strategy,
            success=success,
            reward=reward,
            reverted=reverted,
        )
        self.exploration_history.append(result)
        
        # Update known-good strategies
        if success and reward > 0.7 and strategy not in self.known_good_strategies:
            self.known_good_strategies.append(strategy)
    
    def get_exploration_stats(self) -> Dict[str, Any]:
        """Get exploration performance statistics."""
        if not self.exploration_history:
            return {
                "total_explorations": 0,
                "success_rate": 0.0,
                "average_reward": 0.0,
                "reversion_rate": 0.0,
            }
        
        total = len(self.exploration_history)
        successes = sum(1 for r in self.exploration_history if r.success)
        reversions = sum(1 for r in self.exploration_history if r.reverted)
        avg_reward = sum(r.reward for r in self.exploration_history) / total
        
        return {
            "total_explorations": total,
            "success_rate": successes / total,
            "average_reward": avg_reward,
            "reversion_rate": reversions / total,
            "known_good_strategies": len(self.known_good_strategies),
        }
    
    def evaluate(self, action: Dict[str, Any], context: Dict[str, Any]) -> LayerResult:
        """
        Entry point for pipeline composition.
        
        Decides whether to permit exploration and enforces safety bounds.
        """
        # Check if context is safe for exploration
        is_safe, unsafe_reason = self.is_safe_to_explore(context)
        
        if not is_safe:
            return LayerResult(
                layer="exploration",
                passed=False,
                reason=f"Exploration unsafe: {unsafe_reason}",
                metadata={
                    "mode": self.mode.value,
                    "safe_to_explore": False,
                    "reason": unsafe_reason,
                },
                timestamp=time.time(),
            )
        
        # Decide exploration vs exploitation
        will_explore = self.should_explore()
        
        stats = self.get_exploration_stats()
        
        return LayerResult(
            layer="exploration",
            passed=True,
            reason=f"{'Exploring' if will_explore else 'Exploiting'} - safe to proceed",
            metadata={
                "mode": self.mode.value,
                "will_explore": will_explore,
                "exploration_rate": self.exploration_rate,
                "stats": stats,
            },
            timestamp=time.time(),
        )
    
    def set_mode(self, mode: ExplorationMode):
        """Change exploration mode."""
        self.mode = mode
    
    def set_exploration_rate(self, rate: float):
        """Set exploration rate (0-1)."""
        self.exploration_rate = max(0.0, min(1.0, rate))


# Module-level instance (with deterministic seed for testing)
_exploration = ExplorationLayer(seed=42)


def is_safe_to_explore(context: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """Check safety using global instance."""
    return _exploration.is_safe_to_explore(context)


def should_explore() -> bool:
    """Decide exploration using global instance."""
    return _exploration.should_explore()


def record_exploration(strategy: str, success: bool, reward: float, reverted: bool = False):
    """Record exploration using global instance."""
    _exploration.record_exploration(strategy, success, reward, reverted)


def evaluate(action: Dict[str, Any], context: Dict[str, Any]) -> LayerResult:
    """Standalone evaluation."""
    return _exploration.evaluate(action, context)


def get_exploration_stats() -> Dict[str, Any]:
    """Get stats from global instance."""
    return _exploration.get_exploration_stats()
