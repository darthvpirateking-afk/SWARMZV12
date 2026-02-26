"""
Uplift Layer (P2.2 - Progressive Enhancement)

Enables progressive capability unlocking based on system maturity.
Gradually releases advanced features as confidence increases.

Design:
- Track system maturity metrics
- Define capability tiers with unlock conditions
- Progressive feature enablement
- Rollback on regression detection
"""

import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum

from core.reversible import LayerResult


class CapabilityTier(str, Enum):
    """Capability maturity tiers."""
    BASIC = "basic"          # Always available
    INTERMEDIATE = "intermediate"  # Unlocked after proving stability
    ADVANCED = "advanced"    # Requires high confidence
    EXPERIMENTAL = "experimental"  # Highest tier, bleeding edge


@dataclass
class Capability:
    """A system capability that can be unlocked."""
    name: str
    tier: CapabilityTier
    unlock_conditions: Dict[str, Any]  # Min requirements
    unlocked: bool = False
    unlocked_at: Optional[float] = None
    locked_reason: Optional[str] = None


@dataclass
class MaturityMetrics:
    """System maturity indicators."""
    uptime_hours: float = 0.0
    successful_actions: int = 0
    failed_actions: int = 0
    rollback_count: int = 0
    average_confidence: float = 0.0
    
    def success_rate(self) -> float:
        """Calculate success rate."""
        total = self.successful_actions + self.failed_actions
        if total == 0:
            return 0.0
        return self.successful_actions / total


class UpliftLayer:
    """
    Progressive capability enhancement engine.
    
    Manages gradual feature unlocking based on demonstrated maturity.
    """
    
    def __init__(self):
        self.capabilities: Dict[str, Capability] = {}
        self.maturity = MaturityMetrics()
        self.start_time = time.time()
        self._load_default_capabilities()
    
    def _load_default_capabilities(self):
        """Initialize with baseline capability tiers."""
        # BASIC tier - always unlocked
        self.add_capability(Capability(
            name="basic_execution",
            tier=CapabilityTier.BASIC,
            unlock_conditions={},
            unlocked=True,
            unlocked_at=time.time(),
        ))
        
        # INTERMEDIATE tier - needs 10+ successful actions, 80% success rate
        self.add_capability(Capability(
            name="parallel_execution",
            tier=CapabilityTier.INTERMEDIATE,
            unlock_conditions={
                "successful_actions": 10,
                "success_rate": 0.8,
            },
        ))
        
        # ADVANCED tier - needs 50+ successful, 90% success, 1hr uptime
        self.add_capability(Capability(
            name="autonomous_planning",
            tier=CapabilityTier.ADVANCED,
            unlock_conditions={
                "successful_actions": 50,
                "success_rate": 0.9,
                "uptime_hours": 1.0,
            },
        ))
        
        # EXPERIMENTAL tier - highest bar
        self.add_capability(Capability(
            name="self_modification",
            tier=CapabilityTier.EXPERIMENTAL,
            unlock_conditions={
                "successful_actions": 100,
                "success_rate": 0.95,
                "uptime_hours": 24.0,
                "rollback_count_max": 5,
            },
        ))
    
    def add_capability(self, capability: Capability):
        """Add a capability to the system."""
        self.capabilities[capability.name] = capability
    
    def update_maturity(self, success: bool, confidence: float = 0.0, rolled_back: bool = False):
        """Update maturity metrics after action execution."""
        if success:
            self.maturity.successful_actions += 1
        else:
            self.maturity.failed_actions += 1
        
        if rolled_back:
            self.maturity.rollback_count += 1
        
        # Update running average confidence
        total = self.maturity.successful_actions + self.maturity.failed_actions
        if total > 0:
            self.maturity.average_confidence = (
                (self.maturity.average_confidence * (total - 1) + confidence) / total
            )
        
        # Update uptime
        self.maturity.uptime_hours = (time.time() - self.start_time) / 3600.0
    
    def check_unlock_conditions(self, capability: Capability) -> tuple[bool, Optional[str]]:
        """Check if conditions are met to unlock a capability."""
        if capability.unlocked:
            return True, None
        
        conditions = capability.unlock_conditions
        
        # Check each condition
        if "successful_actions" in conditions:
            if self.maturity.successful_actions < conditions["successful_actions"]:
                return False, f"Need {conditions['successful_actions']} successful actions (have {self.maturity.successful_actions})"
        
        if "success_rate" in conditions:
            if self.maturity.success_rate() < conditions["success_rate"]:
                return False, f"Need {conditions['success_rate']*100}% success rate (have {self.maturity.success_rate()*100:.1f}%)"
        
        if "uptime_hours" in conditions:
            if self.maturity.uptime_hours < conditions["uptime_hours"]:
                return False, f"Need {conditions['uptime_hours']}h uptime (have {self.maturity.uptime_hours:.1f}h)"
        
        if "rollback_count_max" in conditions:
            if self.maturity.rollback_count > conditions["rollback_count_max"]:
                return False, f"Too many rollbacks ({self.maturity.rollback_count} > {conditions['rollback_count_max']})"
        
        if "average_confidence" in conditions:
            if self.maturity.average_confidence < conditions["average_confidence"]:
                return False, f"Need {conditions['average_confidence']} avg confidence (have {self.maturity.average_confidence:.2f})"
        
        # All conditions met
        return True, None
    
    def evaluate_unlocks(self) -> List[Capability]:
        """Check all locked capabilities and attempt to unlock them."""
        newly_unlocked = []
        
        for capability in self.capabilities.values():
            if not capability.unlocked:
                can_unlock, reason = self.check_unlock_conditions(capability)
                
                if can_unlock:
                    capability.unlocked = True
                    capability.unlocked_at = time.time()
                    capability.locked_reason = None
                    newly_unlocked.append(capability)
                else:
                    capability.locked_reason = reason
        
        return newly_unlocked
    
    def is_capability_unlocked(self, capability_name: str) -> bool:
        """Check if a specific capability is unlocked."""
        capability = self.capabilities.get(capability_name)
        if capability is None:
            return False
        return capability.unlocked
    
    def evaluate(self, action: Dict[str, Any], context: Dict[str, Any]) -> LayerResult:
        """
        Entry point for pipeline composition.
        
        Updates maturity and evaluates capability unlocks.
        """
        # Extract execution result if present
        success = context.get("success", True)
        confidence = context.get("confidence", 0.0)
        rolled_back = context.get("rolled_back", False)
        
        # Update maturity
        self.update_maturity(success, confidence, rolled_back)
        
        # Check for new unlocks
        newly_unlocked = self.evaluate_unlocks()
        
        if newly_unlocked:
            return LayerResult(
                layer="uplift",
                passed=True,
                reason=f"Capabilities unlocked: {', '.join(c.name for c in newly_unlocked)}",
                metadata={
                    "newly_unlocked": [c.name for c in newly_unlocked],
                    "total_unlocked": sum(1 for c in self.capabilities.values() if c.unlocked),
                    "maturity": {
                        "success_rate": self.maturity.success_rate(),
                        "uptime_hours": self.maturity.uptime_hours,
                    },
                },
                timestamp=time.time(),
            )
        
        return LayerResult(
            layer="uplift",
            passed=True,
            reason="Maturity updated, no new unlocks",
            metadata={
                "success_rate": self.maturity.success_rate(),
                "successful_actions": self.maturity.successful_actions,
                "unlocked_count": sum(1 for c in self.capabilities.values() if c.unlocked),
            },
            timestamp=time.time(),
        )
    
    def get_locked_capabilities(self) -> List[Capability]:
        """Get all capabilities that are still locked."""
        return [c for c in self.capabilities.values() if not c.unlocked]
    
    def get_unlocked_capabilities(self) -> List[Capability]:
        """Get all unlocked capabilities."""
        return [c for c in self.capabilities.values() if c.unlocked]


# Module-level instance
_uplift = UpliftLayer()


def update_maturity(success: bool, confidence: float = 0.0, rolled_back: bool = False):
    """Update maturity using global instance."""
    _uplift.update_maturity(success, confidence, rolled_back)


def is_capability_unlocked(capability_name: str) -> bool:
    """Check capability status using global instance."""
    return _uplift.is_capability_unlocked(capability_name)


def evaluate(action: Dict[str, Any], context: Dict[str, Any]) -> LayerResult:
    """Standalone evaluation."""
    return _uplift.evaluate(action, context)


def get_locked_capabilities() -> List[Capability]:
    """Get locked capabilities."""
    return _uplift.get_locked_capabilities()


def get_unlocked_capabilities() -> List[Capability]:
    """Get unlocked capabilities."""
    return _uplift.get_unlocked_capabilities()
