"""
Tests for Boundaries Layer (P1.4)

Validates domain boundary enforcement and crossing rules.
"""

import pytest
from core.boundaries import BoundariesLayer, BoundaryRule, DomainType


def test_same_domain_allowed():
    """Same-domain interactions should always be allowed."""
    boundaries = BoundariesLayer()

    result = boundaries.check_boundary_crossing(
        {"action_type": "read"},
        {"from_domain": "data", "to_domain": "data"},
    )

    assert result.passed is True
    assert "Same domain" in result.reason


def test_observation_always_allowed():
    """All domains should be able to observe (read-only)."""
    boundaries = BoundariesLayer()

    # Control -> Observation
    result = boundaries.check_boundary_crossing(
        {"action_type": "log"},
        {"from_domain": "control", "to_domain": "observation"},
    )

    assert result.passed is True


def test_control_to_execution_requires_interface():
    """Control -> Execution should require an interface."""
    boundaries = BoundariesLayer()

    # Without interface
    result1 = boundaries.check_boundary_crossing(
        {"action_type": "execute"},
        {"from_domain": "control", "to_domain": "execution"},
    )

    assert result1.passed is False
    assert "requires interface" in result1.reason.lower()

    # With interface
    result2 = boundaries.check_boundary_crossing(
        {"action_type": "execute"},
        {
            "from_domain": "control",
            "to_domain": "execution",
            "interface": "command_api",
        },
    )

    assert result2.passed is True


def test_execution_to_control_blocked():
    """Execution -> Control should be blocked (no reverse flow)."""
    boundaries = BoundariesLayer()

    result = boundaries.check_boundary_crossing(
        {"action_type": "modify_control"},
        {"from_domain": "execution", "to_domain": "control"},
    )

    assert result.passed is False
    assert "blocked" in result.reason.lower()


def test_security_can_inspect_all():
    """Security domain should be able to inspect all others."""
    boundaries = BoundariesLayer()

    for domain in ["data", "control", "execution", "observation"]:
        result = boundaries.check_boundary_crossing(
            {"action_type": "inspect"},
            {"from_domain": "security", "to_domain": domain},
        )

        assert result.passed is True, f"Security should be able to inspect {domain}"


def test_external_to_control_blocked():
    """External -> Control should be blocked (unless through security)."""
    boundaries = BoundariesLayer()

    result = boundaries.check_boundary_crossing(
        {"action_type": "command"},
        {"from_domain": "external", "to_domain": "control"},
    )

    assert result.passed is False


def test_no_rule_defaults_deny():
    """Unlisted boundary crossings should be denied by default."""
    boundaries = BoundariesLayer()
    boundaries.rules.clear()  # Remove all rules

    result = boundaries.check_boundary_crossing(
        {"action_type": "test"},
        {"from_domain": "data", "to_domain": "control"},
    )

    assert result.passed is False
    assert "No boundary rule" in result.reason


def test_crossing_log_recorded():
    """Boundary crossings should be logged when audit=True."""
    boundaries = BoundariesLayer()
    boundaries.clear_crossing_log()

    # Allowed crossing
    boundaries.check_boundary_crossing(
        {"action_type": "log"},
        {"from_domain": "control", "to_domain": "observation"},
    )

    log = boundaries.get_crossing_log()
    assert len(log) >= 1
    assert log[-1].from_domain == DomainType.CONTROL
    assert log[-1].to_domain == DomainType.OBSERVATION
    assert log[-1].allowed is True


def test_crossing_log_filter_by_domain():
    """Should be able to filter crossing log by domain."""
    boundaries = BoundariesLayer()
    boundaries.clear_crossing_log()

    # Multiple crossings
    boundaries.check_boundary_crossing(
        {"action_type": "log"},
        {"from_domain": "control", "to_domain": "observation"},
    )
    boundaries.check_boundary_crossing(
        {"action_type": "log"},
        {"from_domain": "data", "to_domain": "observation"},
    )

    # Filter by from_domain
    control_crossings = boundaries.get_crossing_log(from_domain=DomainType.CONTROL)
    assert all(c.from_domain == DomainType.CONTROL for c in control_crossings)

    # Filter by to_domain
    obs_crossings = boundaries.get_crossing_log(to_domain=DomainType.OBSERVATION)
    assert all(c.to_domain == DomainType.OBSERVATION for c in obs_crossings)


def test_crossing_log_filter_by_allowed():
    """Should be able to filter by allowed/denied status."""
    boundaries = BoundariesLayer()
    boundaries.clear_crossing_log()

    # Allowed crossing
    boundaries.check_boundary_crossing(
        {"action_type": "log"},
        {"from_domain": "control", "to_domain": "observation"},
    )

    # Denied crossing
    boundaries.check_boundary_crossing(
        {"action_type": "modify"},
        {"from_domain": "execution", "to_domain": "control"},
    )

    # Filter allowed
    allowed_log = boundaries.get_crossing_log(allowed=True)
    assert all(c.allowed for c in allowed_log)

    # Filter denied
    denied_log = boundaries.get_crossing_log(allowed=False)
    assert all(not c.allowed for c in denied_log)


def test_invalid_domain_types():
    """Should handle invalid domain type gracefully."""
    boundaries = BoundariesLayer()

    result = boundaries.check_boundary_crossing(
        {"action_type": "test"},
        {"from_domain": "invalid_domain", "to_domain": "control"},
    )

    assert result.passed is False
    assert "Invalid domain" in result.reason


def test_evaluate_with_boundary_info():
    """Evaluate should check boundaries if domain info present."""
    boundaries = BoundariesLayer()

    result = boundaries.evaluate(
        {"action_type": "test"},
        {"from_domain": "control", "to_domain": "observation"},
    )

    assert result.layer == "boundaries"
    assert result.passed is True


def test_evaluate_without_boundary_info():
    """Evaluate should pass through if no domain info."""
    boundaries = BoundariesLayer()

    result = boundaries.evaluate(
        {"action_type": "test"},
        {},
    )

    assert result.passed is True
    assert "No boundary check required" in result.reason
