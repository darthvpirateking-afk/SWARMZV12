"""
Tests for Sovereign Core (P1.1)

Validates meta-policy override behavior.
"""

import pytest
from core.sovereign import SovereignCore, PolicyRule, LayerResult, OverrideEvent


def test_add_rule_sorts_by_priority():
    """Rules should be sorted by priority (desc)."""
    sovereign = SovereignCore()
    sovereign.rules.clear()  # Start fresh

    sovereign.add_rule(
        PolicyRule(
            name="low",
            priority=10,
            condition="x == 1",
            action="allow",
            reason="Low priority",
        )
    )
    sovereign.add_rule(
        PolicyRule(
            name="high",
            priority=50,
            condition="y == 2",
            action="deny",
            reason="High priority",
        )
    )
    sovereign.add_rule(
        PolicyRule(
            name="medium",
            priority=25,
            condition="z == 3",
            action="allow",
            reason="Medium priority",
        )
    )

    assert sovereign.rules[0].priority == 50
    assert sovereign.rules[1].priority == 25
    assert sovereign.rules[2].priority == 10


def test_evaluate_condition_simple_equality():
    """Condition evaluator should handle basic equality."""
    sovereign = SovereignCore()

    assert sovereign._evaluate_condition(
        "action_type == 'critical'", {"action_type": "critical"}
    )
    assert not sovereign._evaluate_condition(
        "action_type == 'critical'", {"action_type": "normal"}
    )


def test_evaluate_condition_boolean():
    """Condition evaluator should handle boolean values."""
    sovereign = SovereignCore()

    assert sovereign._evaluate_condition(
        "security_violation == True", {"security_violation": True}
    )
    assert not sovereign._evaluate_condition(
        "security_violation == True", {"security_violation": False}
    )


def test_evaluate_condition_inequality():
    """Condition evaluator should handle <= and >=."""
    sovereign = SovereignCore()

    assert sovereign._evaluate_condition(
        "budget_remaining <= 0", {"budget_remaining": 0}
    )
    assert sovereign._evaluate_condition(
        "budget_remaining <= 0", {"budget_remaining": -10}
    )
    assert not sovereign._evaluate_condition(
        "budget_remaining <= 0", {"budget_remaining": 10}
    )


def test_resolve_override_allow_over_deny():
    """High-priority allow should override lower deny."""
    sovereign = SovereignCore()
    sovereign.rules.clear()

    # Add high-priority allow
    sovereign.add_rule(
        PolicyRule(
            name="critical_override",
            priority=100,
            condition="action_type == 'system_critical'",
            action="allow",
            reason="Critical operation",
        )
    )

    # Simulate a lower layer denying
    denial = LayerResult(
        layer="threshold",
        passed=False,
        reason="Budget exhausted",
        metadata={},
        timestamp=0.0,
    )

    result = sovereign.resolve_override(
        denial,
        {"action_type": "system_critical"},
        {},
    )

    assert result.passed is True
    assert result.layer == "sovereign"
    assert "override" in result.reason.lower()
    assert result.metadata["original_decision"] is False


def test_resolve_override_deny_over_allow():
    """High-priority deny should override lower allow."""
    sovereign = SovereignCore()
    sovereign.rules.clear()

    sovereign.add_rule(
        PolicyRule(
            name="security_block",
            priority=50,
            condition="security_violation == True",
            action="deny",
            reason="Security issue detected",
        )
    )

    # Simulate lower layer allowing
    approval = LayerResult(
        layer="scoring",
        passed=True,
        reason="Low risk score",
        metadata={},
        timestamp=0.0,
    )

    result = sovereign.resolve_override(
        approval,
        {},
        {"security_violation": True},
    )

    assert result.passed is False
    assert result.layer == "sovereign"


def test_resolve_override_no_match():
    """No matching rule should return original result."""
    sovereign = SovereignCore()
    sovereign.rules.clear()

    approval = LayerResult(
        layer="integrity",
        passed=True,
        reason="All constraints satisfied",
        metadata={},
        timestamp=0.0,
    )

    result = sovereign.resolve_override(approval, {}, {})

    # Should return original
    assert result.layer == "integrity"
    assert result.passed is True


def test_resolve_override_defer():
    """Defer action should not override."""
    sovereign = SovereignCore()
    sovereign.rules.clear()

    sovereign.add_rule(
        PolicyRule(
            name="defer_rule",
            priority=30,
            condition="action_type == 'normal'",
            action="defer",
            reason="Defer to lower layers",
        )
    )

    approval = LayerResult(
        layer="scoring",
        passed=True,
        reason="Good score",
        metadata={},
        timestamp=0.0,
    )

    result = sovereign.resolve_override(
        approval,
        {"action_type": "normal"},
        {},
    )

    # Should return original (defer doesn't change)
    assert result.layer == "scoring"
    assert result.passed is True


def test_override_history_recording():
    """Override events should be recorded."""
    sovereign = SovereignCore()
    sovereign.rules.clear()
    sovereign.clear_override_history()

    sovereign.add_rule(
        PolicyRule(
            name="test_override",
            priority=100,
            condition="x == 1",
            action="allow",
            reason="Test override",
        )
    )

    denial = LayerResult(
        layer="threshold",
        passed=False,
        reason="Denied",
        metadata={},
        timestamp=0.0,
    )

    sovereign.resolve_override(denial, {"x": 1}, {})

    history = sovereign.get_override_history()
    assert len(history) == 1
    assert history[0].overriding_rule == "test_override"
    assert history[0].original_decision is False
    assert history[0].new_decision is True


def test_evaluate_standalone():
    """Standalone evaluate should apply first matching rule."""
    sovereign = SovereignCore()
    sovereign.rules.clear()

    sovereign.add_rule(
        PolicyRule(
            name="block_dangerous",
            priority=50,
            condition="danger_level >= 5",
            action="deny",
            reason="Danger level too high",
        )
    )

    result = sovereign.evaluate({}, {"danger_level": 8})

    assert result.passed is False
    assert result.metadata["rule_applied"] == "block_dangerous"


def test_evaluate_default_allow():
    """No matching rules should default to allow."""
    sovereign = SovereignCore()
    sovereign.rules.clear()

    result = sovereign.evaluate({}, {})

    assert result.passed is True
    assert "default allow" in result.reason.lower()


def test_priority_resolution_order():
    """Higher priority rules should be checked first."""
    sovereign = SovereignCore()
    sovereign.rules.clear()

    # Add in reverse order
    sovereign.add_rule(
        PolicyRule(
            name="low_priority",
            priority=10,
            condition="x == 1",
            action="deny",
            reason="Low priority deny",
        )
    )
    sovereign.add_rule(
        PolicyRule(
            name="high_priority",
            priority=100,
            condition="x == 1",
            action="allow",
            reason="High priority allow",
        )
    )

    result = sovereign.evaluate({"x": 1}, {})

    # High priority should win
    assert result.passed is True
    assert result.metadata["rule_applied"] == "high_priority"
