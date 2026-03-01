# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
tests/test_integrity.py — Integrity Layer Tests

Validates structural constraints and architectural restraint enforcement.
"""

from core.integrity import IntegrityLayer, enforce_constraint, evaluate


def test_check_cyclic_dependency_none():
    """Action with no dependencies should pass."""
    layer = IntegrityLayer()
    action = {"id": "action_1", "dependencies": []}

    result = layer.check_cyclic_dependency(action)

    assert result.passed
    assert result.layer == "integrity"


def test_check_cyclic_dependency_self_reference():
    """Self-dependency should fail."""
    layer = IntegrityLayer()
    action = {"id": "action_1", "dependencies": ["action_1"]}

    result = layer.check_cyclic_dependency(action)

    assert not result.passed
    assert "self-dependency" in result.reason.lower()


def test_check_cross_domain_mutation_same_domain():
    """Same-domain operations should pass."""
    layer = IntegrityLayer()
    action = {
        "source_domain": "core",
        "target_domain": "core",
        "type": "write",
    }

    result = layer.check_cross_domain_mutation(action)

    assert result.passed
    assert "same-domain" in result.reason.lower()


def test_check_cross_domain_mutation_no_interface():
    """Cross-domain write without interface should fail."""
    layer = IntegrityLayer()
    action = {
        "source_domain": "core",
        "target_domain": "nexusmon",
        "type": "write",
        "has_interface_contract": False,
    }

    result = layer.check_cross_domain_mutation(action)

    assert not result.passed
    assert "without interface" in result.reason.lower()


def test_check_cross_domain_mutation_with_interface():
    """Cross-domain operation with interface should pass."""
    layer = IntegrityLayer()
    action = {
        "source_domain": "core",
        "target_domain": "nexusmon",
        "type": "write",
        "has_interface_contract": True,
    }

    result = layer.check_cross_domain_mutation(action)

    assert result.passed


def test_check_stub_exposure_internal():
    """Internal actions can have stubs."""
    layer = IntegrityLayer()
    action = {
        "code": "pass  # TODO: implement later",
        "is_public_api": False,
    }

    result = layer.check_stub_exposure(action)

    assert result.passed


def test_check_stub_exposure_public_api():
    """Public API with stub pattern should fail."""
    layer = IntegrityLayer()
    action = {
        "code": "return {'status': 'stub'}",
        "description": "This is a stub implementation for now",
        "is_public_api": True,
    }

    result = layer.check_stub_exposure(action)

    assert not result.passed
    assert "stub" in result.reason.lower()


def test_enforce_constraint_all_pass():
    """All checks passing should return overall pass."""
    layer = IntegrityLayer()
    action = {
        "id": "action_1",
        "dependencies": ["action_0"],
        "source_domain": "core",
        "target_domain": "core",
        "type": "read",
        "is_public_api": False,
    }

    result = layer.enforce_constraint(action)

    assert result.passed
    assert result.metadata["total_checks"] == 3


def test_enforce_constraint_with_violation():
    """First violation should be returned."""
    layer = IntegrityLayer()
    action = {
        "id": "action_1",
        "dependencies": ["action_1"],  # Self-dependency
        "source_domain": "core",
        "target_domain": "nexusmon",
        "type": "write",
        "has_interface_contract": False,
        "is_public_api": False,
    }

    result = layer.enforce_constraint(action)

    assert not result.passed
    assert result.metadata["violations"] >= 1


def test_evaluate_wrapper():
    """evaluate() should call enforce_constraint()."""
    action = {
        "id": "action_1",
        "dependencies": [],
        "source_domain": "core",
        "target_domain": "core",
        "type": "read",
        "is_public_api": False,
    }
    context = {}

    result = evaluate(action, context)

    assert result.layer == "integrity"
    assert result.passed
