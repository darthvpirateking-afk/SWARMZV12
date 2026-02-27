"""
Shadow Channel (P1.2 - Governance Principle #3: The Hidden Way)

Opaque decision observability layer.
Decisions may be hidden from users, but their trails are fully logged.

Design:
- Record decisions that don't surface reasoning to users
- Full telemetry for internal audit while user sees minimal info
- Track "silent rejections" and "quiet approvals"
- Integrates with logging infrastructure for forensic analysis
"""

import time
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum

from core.reversible import LayerResult

logger = logging.getLogger(__name__)


class OpacityLevel(str, Enum):
    """How much reasoning is revealed to the user."""

    TRANSPARENT = "transparent"  # Full reasoning shown
    PARTIAL = "partial"  # Summary only
    OPAQUE = "opaque"  # No reasoning shown, only decision
    SILENT = "silent"  # Decision applied without user awareness


@dataclass
class ShadowDecision:
    """A decision made in the shadow - user sees minimal info."""

    timestamp: float
    decision_id: str
    opacity_level: OpacityLevel
    layer: str
    passed: bool
    internal_reason: str  # Full reasoning (logged, not shown)
    user_facing_message: str  # What the user sees
    metadata: Dict[str, Any] = field(default_factory=dict)
    triggered_by: Optional[str] = None  # Which rule/check triggered this


class ShadowChannel:
    """
    Observability layer for opaque decisions.

    Records the full trail of decisions that are hidden from users.
    """

    def __init__(self):
        self.shadow_log: List[ShadowDecision] = []
        self._decision_counter = 0

    def record_shadow_decision(
        self,
        layer: str,
        passed: bool,
        internal_reason: str,
        user_facing_message: str,
        opacity_level: OpacityLevel,
        metadata: Optional[Dict[str, Any]] = None,
        triggered_by: Optional[str] = None,
    ) -> ShadowDecision:
        """
        Record a decision made in the shadow.

        Args:
            layer: Which governance layer made the decision
            passed: Whether the action was allowed
            internal_reason: Full technical reasoning (logged only)
            user_facing_message: Simplified message shown to user
            opacity_level: How much is revealed
            metadata: Additional context
            triggered_by: Which rule/check triggered this

        Returns:
            ShadowDecision record
        """
        self._decision_counter += 1
        decision = ShadowDecision(
            timestamp=time.time(),
            decision_id=f"shadow_{self._decision_counter}",
            opacity_level=opacity_level,
            layer=layer,
            passed=passed,
            internal_reason=internal_reason,
            user_facing_message=user_facing_message,
            metadata=metadata or {},
            triggered_by=triggered_by,
        )

        self.shadow_log.append(decision)

        # Log full details internally
        logger.info(
            f"[SHADOW] {decision.decision_id} | {layer} | "
            f"{'PASS' if passed else 'DENY'} | Opacity: {opacity_level.value} | "
            f"Internal: {internal_reason}"
        )

        return decision

    def wrap_layer_result(
        self,
        result: LayerResult,
        opacity_level: OpacityLevel,
        user_facing_message: Optional[str] = None,
    ) -> LayerResult:
        """
        Wrap a layer result with shadow tracking.

        Records the full decision in shadow log, then returns a potentially
        sanitized version for the user.
        """
        # Record in shadow
        shadow = self.record_shadow_decision(
            layer=result.layer,
            passed=result.passed,
            internal_reason=result.reason,
            user_facing_message=user_facing_message
            or self._generate_user_message(result, opacity_level),
            opacity_level=opacity_level,
            metadata=result.metadata,
        )

        # Return sanitized result based on opacity
        if opacity_level == OpacityLevel.TRANSPARENT:
            # User sees everything, but add shadow ID for traceability
            return LayerResult(
                layer=result.layer,
                passed=result.passed,
                reason=result.reason,
                metadata={**result.metadata, "shadow_id": shadow.decision_id},
                timestamp=result.timestamp,
            )

        elif opacity_level == OpacityLevel.PARTIAL:
            # User sees summary
            return LayerResult(
                layer=result.layer,
                passed=result.passed,
                reason=shadow.user_facing_message,
                metadata={"shadow_id": shadow.decision_id},
                timestamp=result.timestamp,
            )

        elif opacity_level == OpacityLevel.OPAQUE:
            # User sees only pass/fail
            return LayerResult(
                layer=result.layer,
                passed=result.passed,
                reason="Decision made" if result.passed else "Action not permitted",
                metadata={"shadow_id": shadow.decision_id},
                timestamp=result.timestamp,
            )

        else:  # SILENT
            # No indication to user (logged only)
            return LayerResult(
                layer="shadow",
                passed=result.passed,
                reason="",  # Empty reason
                metadata={"shadow_id": shadow.decision_id, "silent": True},
                timestamp=result.timestamp,
            )

    def _generate_user_message(
        self, result: LayerResult, opacity_level: OpacityLevel
    ) -> str:
        """Generate appropriate user-facing message based on opacity."""
        if opacity_level == OpacityLevel.TRANSPARENT:
            return result.reason

        elif opacity_level == OpacityLevel.PARTIAL:
            # Simplify technical details
            if result.passed:
                return f"{result.layer.capitalize()} checks passed"
            else:
                return f"{result.layer.capitalize()} constraints not met"

        elif opacity_level == OpacityLevel.OPAQUE:
            return "Decision made" if result.passed else "Action not permitted"

        else:  # SILENT
            return ""

    def query_shadow_log(
        self,
        layer: Optional[str] = None,
        passed: Optional[bool] = None,
        opacity_level: Optional[OpacityLevel] = None,
        limit: int = 100,
    ) -> List[ShadowDecision]:
        """
        Query shadow log with filters.

        Used for forensic analysis and audit trails.
        """
        results = self.shadow_log[-limit * 2 :]  # Over-fetch for filtering

        if layer is not None:
            results = [d for d in results if d.layer == layer]

        if passed is not None:
            results = [d for d in results if d.passed == passed]

        if opacity_level is not None:
            results = [d for d in results if d.opacity_level == opacity_level]

        return results[-limit:]

    def get_decision_by_id(self, decision_id: str) -> Optional[ShadowDecision]:
        """Retrieve a specific shadow decision by ID."""
        for decision in reversed(self.shadow_log):
            if decision.decision_id == decision_id:
                return decision
        return None

    def evaluate(self, action: Dict[str, Any], context: Dict[str, Any]) -> LayerResult:
        """
        Entry point for pipeline composition.

        Shadow channel is typically used as a wrapper, not standalone.
        This method exists for consistency but mostly passes through.
        """
        # Shadow channel doesn't block - it observes
        return LayerResult(
            layer="shadow",
            passed=True,
            reason="Shadow channel active",
            metadata={"shadow_log_size": len(self.shadow_log)},
            timestamp=time.time(),
        )

    def clear_shadow_log(self):
        """Clear shadow log (for testing or log rotation)."""
        self.shadow_log.clear()
        self._decision_counter = 0


# Module-level instance
_shadow = ShadowChannel()


def record_shadow_decision(
    layer: str,
    passed: bool,
    internal_reason: str,
    user_facing_message: str,
    opacity_level: OpacityLevel,
    metadata: Optional[Dict[str, Any]] = None,
    triggered_by: Optional[str] = None,
) -> ShadowDecision:
    """Record a shadow decision using global instance."""
    return _shadow.record_shadow_decision(
        layer,
        passed,
        internal_reason,
        user_facing_message,
        opacity_level,
        metadata,
        triggered_by,
    )


def wrap_layer_result(
    result: LayerResult,
    opacity_level: OpacityLevel,
    user_facing_message: Optional[str] = None,
) -> LayerResult:
    """Wrap a layer result with shadow tracking."""
    return _shadow.wrap_layer_result(result, opacity_level, user_facing_message)


def query_shadow_log(
    layer: Optional[str] = None,
    passed: Optional[bool] = None,
    opacity_level: Optional[OpacityLevel] = None,
    limit: int = 100,
) -> List[ShadowDecision]:
    """Query shadow log."""
    return _shadow.query_shadow_log(layer, passed, opacity_level, limit)


def get_decision_by_id(decision_id: str) -> Optional[ShadowDecision]:
    """Get specific decision by ID."""
    return _shadow.get_decision_by_id(decision_id)


def evaluate(action: Dict[str, Any], context: Dict[str, Any]) -> LayerResult:
    """Standalone evaluation (pass-through)."""
    return _shadow.evaluate(action, context)
