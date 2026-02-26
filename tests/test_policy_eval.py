"""Tests for the Policy Evaluator (P0.1)"""

import pytest
from core.policy_eval import evaluate_action, PolicyDecision, PolicyRule

# --------------------------------------------------------------------------
# Test Fixtures
# --------------------------------------------------------------------------

@pytest.fixture
def sample_action() -> dict:
    """A generic action for testing."""
    return {"type": "DEPLOY_MODEL", "model_id": "test-model-v1"}

# --------------------------------------------------------------------------
# Basic Evaluation Tests
# --------------------------------------------------------------------------

def test_default_allow(sample_action):
    """Test that a low-risk, low-cost action is admitted by default."""
    context = {"risk_score": 0.1, "cost_score": 0.1, "is_reversible": True, "source_trust": "trusted"}
    decision = evaluate_action(sample_action, context)
    assert decision.admit is True
    assert decision.severity == "S1"
    assert "Default policy: allow" in decision.reasons

def test_deny_high_risk_non_reversible(sample_action):
    """Test S4 deny: high risk and not reversible."""
    context = {"risk_score": 0.95, "is_reversible": False}
    decision = evaluate_action(sample_action, context)
    assert decision.admit is False
    assert decision.severity == "S4"
    assert "High-risk action is not reversible" in decision.reasons

def test_deny_critical_impact(sample_action):
    """Test S4 deny: action has a 'critical' impact tag."""
    context = {"impact_tags": ["critical", "data-access"]}
    decision = evaluate_action(sample_action, context)
    assert decision.admit is False
    assert decision.severity == "S4"
    assert "Action has 'critical' impact tag" in decision.reasons

def test_deny_excessive_cost(sample_action):
    """Test S3 deny: cost score is too high."""
    context = {"cost_score": 0.98}
    decision = evaluate_action(sample_action, context)
    assert decision.admit is False
    assert decision.severity == "S3"
    assert "Action cost exceeds 95% threshold" in decision.reasons

def test_deny_untrusted_source(sample_action):
    """Test S3 deny: source of the action is untrusted."""
    context = {"source_trust": "untrusted"}
    decision = evaluate_action(sample_action, context)
    assert decision.admit is False
    assert decision.severity == "S3"
    assert "Action source is untrusted" in decision.reasons

def test_admit_high_risk_but_reversible(sample_action):
    """Test S2 admit: high risk is allowed if it's reversible."""
    context = {"risk_score": 0.85, "is_reversible": True, "source_trust": "verified"}
    decision = evaluate_action(sample_action, context)
    assert decision.admit is True
    assert decision.severity == "S2"
    assert "High-risk action, proceed with caution (reversible)" in decision.reasons

def test_admit_moderate_cost(sample_action):
    """Test S2 admit: moderate cost is allowed with a warning."""
    context = {"cost_score": 0.75, "source_trust": "verified"}
    decision = evaluate_action(sample_action, context)
    assert decision.admit is True
    assert decision.severity == "S2"
    assert "Action has moderate cost" in decision.reasons

# --------------------------------------------------------------------------
# Custom Rule Tests
# --------------------------------------------------------------------------

def test_custom_ruleset_overrides_default(sample_action):
    """Test that a custom ruleset can completely change the logic."""
    custom_rules = [
        PolicyRule(
            name="deny_all_deploys",
            condition="action.get('type') == 'DEPLOY_MODEL'",
            on_true=PolicyDecision(admit=False, score=1.0, reasons=["All deploys are forbidden by custom policy"], severity="S4")
        ),
        PolicyRule(
            name="default_allow_custom",
            condition="True",
            on_true=PolicyDecision(admit=True, score=0.0, reasons=["Custom default allow"], severity="S1")
        ),
    ]
    context = {"risk_score": 0.1} # This would normally pass
    decision = evaluate_action(sample_action, context, rules=custom_rules)
    assert decision.admit is False
    assert "All deploys are forbidden by custom policy" in decision.reasons

def test_rule_order_matters(sample_action):
    """The first matching rule should win."""
    custom_rules = [
        PolicyRule(
            name="specific_deny",
            condition="context.get('risk_score', 0) > 0.5",
            on_true=PolicyDecision(admit=False, score=0.6, reasons=["Denied by specific rule"], severity="S3")
        ),
        PolicyRule(
            name="generic_allow",
            condition="context.get('risk_score', 0) > 0.1",
            on_true=PolicyDecision(admit=True, score=0.2, reasons=["Allowed by generic rule"], severity="S1")
        ),
    ]
    context = {"risk_score": 0.6}
    decision = evaluate_action(sample_action, context, rules=custom_rules)
    assert decision.admit is False
    assert "Denied by specific rule" in decision.reasons

# --------------------------------------------------------------------------
# Edge Case Tests
# --------------------------------------------------------------------------

def test_empty_context_hits_default_allow(sample_action):
    """An empty context should still be handled gracefully."""
    context = {"source_trust": "verified"} # Must satisfy the trust rule
    decision = evaluate_action(sample_action, context)
    assert decision.admit is True
    assert decision.severity == "S1"

def test_no_matching_rule_falls_through(sample_action):
    """If no rule matches (e.g., no default), it should deny."""
    custom_rules = [
        PolicyRule(
            name="only_rule",
            condition="context.get('risk_score', 0) > 0.9",
            on_true=PolicyDecision(admit=True, score=0.9, reasons=["Only if very risky"], severity="S2")
        )
    ]
    context = {"risk_score": 0.5}
    decision = evaluate_action(sample_action, context, rules=custom_rules)
    assert decision.admit is False
    assert decision.severity == "S4"
    assert "Fell through all rules; default deny" in decision.reasons

def test_malformed_condition_is_false():
    """A malformed condition in a custom rule should evaluate to False."""
    # This condition is invalid for the simple parser
    custom_rules = [
        PolicyRule(
            name="bad_rule",
            condition="risk_score > 0.5 and cost_score < 0.2",
            on_true=PolicyDecision(admit=False, score=1.0, reasons=["Bad rule triggered"], severity="S4")
        ),
        PolicyRule(
            name="default_allow",
            condition="True",
            on_true=PolicyDecision(admit=True, score=0.1, reasons=["Default allow"], severity="S1")
        ),
    ]
    context = {"risk_score": 0.6, "cost_score": 0.1}
    decision = evaluate_action({}, context, rules=custom_rules)
    assert decision.admit is True
    assert "Default allow" in decision.reasons
