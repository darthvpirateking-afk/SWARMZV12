"""
Bounded Sovereign Classifier (P1.1 - Governance Principle #4)

Meta-policy layer that classifies lower governance outcomes into
bounded decision bands. Implements deterministic rule resolution.

Design:
- Non-executive classification: Evaluates state and returns a Decision.
- S1-S4 Severity Bands: Categorizes risk levels.
- Mandatory Escalation: Critical operations cannot be "auto-allowed".
- Rank N Singularity Override: Absolute operator authority.
- Glyph Emergence: Sovereign moments that matter leave marks.
"""

import time
import logging
from enum import Enum
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

from core.reversible import LayerResult

logger = logging.getLogger(__name__)


class SovereignOutcome(Enum):
    """Possible outcomes for a sovereign classification."""

    PASS = "PASS"
    ESCALATE = "ESCALATE"
    QUARANTINE = "QUARANTINE"
    DENY = "DENY"


@dataclass
class PolicyRule:
    """A sovereign policy rule with severity and outcome.

    Accepts either the modern *outcome* field (SovereignOutcome) or the legacy
    *action* string ("allow" / "deny" / "defer" / "escalate" / "quarantine").
    """

    name: str
    priority: int
    condition: str
    outcome: SovereignOutcome = SovereignOutcome.PASS
    severity: str = "S4"
    reason: str = ""
    action: str = ""

    def __post_init__(self):
        action_to_outcome = {
            "allow": SovereignOutcome.PASS,
            "deny": SovereignOutcome.DENY,
            "defer": SovereignOutcome.PASS,
            "escalate": SovereignOutcome.ESCALATE,
            "quarantine": SovereignOutcome.QUARANTINE,
        }
        outcome_to_action = {
            SovereignOutcome.PASS: "allow",
            SovereignOutcome.DENY: "deny",
            SovereignOutcome.ESCALATE: "escalate",
            SovereignOutcome.QUARANTINE: "quarantine",
        }
        if self.action:
            self.outcome = action_to_outcome.get(self.action, self.outcome)
        if not self.action:
            self.action = outcome_to_action.get(self.outcome, "allow")


@dataclass
class SovereignDecision:
    """The result of a sovereign classification."""

    outcome: SovereignOutcome
    reason: str
    rule_name: Optional[str] = None
    severity: Optional[str] = None
    timestamp: float = field(default_factory=time.time)


@dataclass
class OverrideEvent:
    """Record of a sovereign override -- logged in the shadow channel."""

    overriding_rule: str
    original_decision: bool
    new_decision: bool
    reason: str = ""
    timestamp: float = field(default_factory=time.time)


class SovereignClassifier:
    """
    Meta-policy engine that classifies lower governance decisions.

    Severity Bands:
    - S1: Critical/Emergency (Immediate escalation required)
    - S2: High Risk (Security/Hard blocks, Quarantine)
    - S3: Medium Risk (Standard policy enforcement)
    - S4: Low Risk (Policy recommendations / Soft limits)
    """

    def __init__(self):
        self.rules: List[PolicyRule] = []
        self._override_history: List[OverrideEvent] = []
        self._glyphs: List[Dict[str, Any]] = []
        self._load_default_rules()

    def _load_default_rules(self):
        """Initialize with baseline sovereign policies using S1-S4 bands."""
        self.add_rule(
            PolicyRule(
                name="nexus_singularity_override",
                priority=1000,
                condition="operator_rank == 'N'",
                outcome=SovereignOutcome.PASS,
                severity="N/A",
                reason="Singularity Override: Rank N operator has absolute authority.",
            )
        )
        self.add_rule(
            PolicyRule(
                name="critical_system_escalation",
                priority=100,
                condition="action_type == 'system_critical'",
                outcome=SovereignOutcome.ESCALATE,
                severity="S1",
                reason="Critical system operation requires human-in-the-loop escalation",
            )
        )
        self.add_rule(
            PolicyRule(
                name="security_quarantine",
                priority=50,
                condition="security_violation == True",
                outcome=SovereignOutcome.QUARANTINE,
                severity="S2",
                reason="Security policy violation: isolation and analysis required",
            )
        )
        self.add_rule(
            PolicyRule(
                name="budget_exhaustion_deny",
                priority=10,
                condition="budget_remaining <= 0",
                outcome=SovereignOutcome.DENY,
                severity="S3",
                reason="Budget depleted: standard operational stop",
            )
        )

    def add_rule(self, rule: PolicyRule):
        """Add a sovereign policy rule."""
        self.rules.append(rule)
        self.rules.sort(key=lambda rule_item: rule_item.priority, reverse=True)
        logger.info(
            "Added sovereign rule: %s (Priority %s, Severity %s)",
            rule.name,
            rule.priority,
            rule.severity,
        )

    def _evaluate_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        """Simple condition evaluator (strictly non-executive)."""
        if "==" in condition:
            key, value = condition.split("==")
            key = key.strip()
            value = value.strip()

            if "." in key:
                parts = key.split(".")
                obj = context
                for part in parts:
                    if isinstance(obj, dict) and part in obj:
                        obj = obj[part]
                    else:
                        return False
                actual_value = obj
            else:
                actual_value = context.get(key)

            if value == "True":
                return actual_value is True
            if value == "False":
                return actual_value is False
            if value.isdigit():
                return actual_value == int(value)

            value = value.strip("'\"")
            return str(actual_value) == value

        if "<=" in condition:
            key, value = condition.split("<=")
            key = key.strip()
            try:
                actual = float(context.get(key, float("inf")))
                limit = float(value.strip())
                return actual <= limit
            except (ValueError, TypeError):
                return False

        if ">=" in condition:
            key, value = condition.split(">=")
            key = key.strip()
            try:
                actual = float(context.get(key, 0))
                limit = float(value.strip())
                return actual >= limit
            except (ValueError, TypeError):
                return False

        return False

    def classify(
        self, layer_result: LayerResult, context: Dict[str, Any]
    ) -> SovereignDecision:
        """Classify a layer result to sovereign outcome bands."""
        eval_context = {
            **context,
            "layer_name": layer_result.layer,
            "layer_passed": layer_result.passed,
        }

        for rule in self.rules:
            if self._evaluate_condition(rule.condition, eval_context):
                logger.warning(
                    "SOVEREIGN CLASSIFIED: %s (%s) -> %s",
                    rule.name,
                    rule.severity,
                    rule.outcome.value,
                )
                return SovereignDecision(
                    outcome=rule.outcome,
                    reason=rule.reason,
                    rule_name=rule.name,
                    severity=rule.severity,
                )

        if layer_result.passed:
            return SovereignDecision(
                outcome=SovereignOutcome.PASS,
                reason="Default sovereign pass (aligned with underlying layer)",
            )

        return SovereignDecision(
            outcome=SovereignOutcome.DENY,
            reason=f"Sovereign adherence to layer denial: {layer_result.reason}",
        )

    def resolve_override(
        self,
        layer_result: LayerResult,
        request_ctx: Dict[str, Any],
        runtime_ctx: Optional[Dict[str, Any]] = None,
    ) -> LayerResult:
        """Legacy API -- resolve an override, returning a LayerResult."""
        ctx = {**(request_ctx or {}), **(runtime_ctx or {})}
        for rule in self.rules:
            if self._evaluate_condition(rule.condition, ctx):
                if rule.action == "defer":
                    return layer_result
                is_pass = rule.action in ("allow", "escalate", "")
                if rule.action == "deny" or rule.outcome == SovereignOutcome.DENY:
                    is_pass = False
                self._override_history.append(
                    OverrideEvent(
                        overriding_rule=rule.name,
                        original_decision=layer_result.passed,
                        new_decision=is_pass,
                        reason=rule.reason,
                    )
                )
                self._check_glyph_emergence(rule, layer_result.passed, is_pass)
                return LayerResult(
                    layer="sovereign",
                    passed=is_pass,
                    reason=f"Sovereign override ({rule.name}): {rule.reason}",
                    metadata={
                        "original_decision": layer_result.passed,
                        "rule_applied": rule.name,
                    },
                    timestamp=time.time(),
                )
        return layer_result

    def evaluate(
        self,
        request_ctx: Dict[str, Any],
        runtime_ctx: Optional[Dict[str, Any]] = None,
    ) -> LayerResult:
        """Standalone evaluation without an existing layer result."""
        ctx = {**(request_ctx or {}), **(runtime_ctx or {})}
        for rule in self.rules:
            if self._evaluate_condition(rule.condition, ctx):
                if rule.action == "defer":
                    continue
                is_pass = rule.action not in ("deny", "quarantine")
                return LayerResult(
                    layer="sovereign",
                    passed=is_pass,
                    reason=rule.reason,
                    metadata={"rule_applied": rule.name},
                    timestamp=time.time(),
                )
        return LayerResult(
            layer="sovereign",
            passed=True,
            reason="Default allow (no matching sovereign rules)",
            metadata={},
            timestamp=time.time(),
        )

    def clear_override_history(self):
        """Clear recorded override events."""
        self._override_history.clear()

    def get_override_history(self) -> List[OverrideEvent]:
        """Return all recorded override events."""
        return list(self._override_history)

    def _check_glyph_emergence(self, rule: PolicyRule, original: bool, final: bool):
        """Track major sovereign reversals as glyph events."""
        if original != final:
            glyph = {
                "trigger": rule.name,
                "original_decision": original,
                "sovereign_decision": final,
                "reason": rule.reason,
                "emerged_at": time.time(),
            }
            self._glyphs.append(glyph)
            logger.info("GLYPH EMERGED: %s -- the system held.", rule.name)

    def get_glyphs(self) -> List[Dict[str, Any]]:
        """Return all emerged glyphs."""
        return list(self._glyphs)


_classifier = SovereignClassifier()


def add_rule(rule: PolicyRule):
    """Add a sovereign policy rule to the global instance."""
    _classifier.add_rule(rule)


def classify(layer_result: LayerResult, context: Dict[str, Any]) -> SovereignDecision:
    """Classify a layer result using the global instance."""
    return _classifier.classify(layer_result, context)


def resolve_override(
    layer_result: LayerResult,
    request_ctx: Dict[str, Any],
    runtime_ctx: Optional[Dict[str, Any]] = None,
) -> LayerResult:
    """Resolve sovereign override using the global instance (legacy API)."""
    return _classifier.resolve_override(layer_result, request_ctx, runtime_ctx)


def evaluate(
    request_ctx: Dict[str, Any],
    runtime_ctx: Optional[Dict[str, Any]] = None,
) -> LayerResult:
    """Evaluate sovereign rules using the global instance (legacy API)."""
    return _classifier.evaluate(request_ctx, runtime_ctx)


SovereignCore = SovereignClassifier
