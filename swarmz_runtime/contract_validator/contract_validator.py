# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
ContractValidator – validates agent contracts/operations before execution.

A "contract" is a dict describing an intended action with required fields.
The validator checks that mandatory fields are present and that optional
policy rules pass before the operation is allowed to proceed.
"""

from typing import Any, Callable, Dict, List, Optional, Tuple


# Validation result type
ValidationResult = Tuple[bool, str]

# A rule is a callable that accepts a contract dict and returns (ok, reason)
RuleFn = Callable[[Dict[str, Any]], ValidationResult]


class ContractValidator:
    """
    Validates operation contracts before they are dispatched to agents.

    Usage::

        validator = ContractValidator()
        ok, reason = validator.validate({"agent": "Partner", "action": "deploy"})

    Custom rules can be added with :meth:`add_rule`.
    """

    # Fields that every contract must contain
    REQUIRED_FIELDS: List[str] = ["agent", "action"]

    def __init__(self):
        self._rules: List[RuleFn] = []
        # Install built-in rules
        self._rules.append(self._rule_required_fields)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_rule(self, rule: RuleFn) -> None:
        """Register an additional validation rule."""
        self._rules.append(rule)

    def validate(self, contract: Dict[str, Any]) -> ValidationResult:
        """
        Run all registered rules against *contract*.

        Returns:
            (True, "ok") if all rules pass.
            (False, <reason>) for the first failing rule.
        """
        if not isinstance(contract, dict):
            return False, "contract must be a dict"

        for rule in self._rules:
            ok, reason = rule(contract)
            if not ok:
                return False, reason

        return True, "ok"

    # ------------------------------------------------------------------
    # Built-in rules
    # ------------------------------------------------------------------

    def _rule_required_fields(self, contract: Dict[str, Any]) -> ValidationResult:
        for field in self.REQUIRED_FIELDS:
            if field not in contract or contract[field] is None:
                return False, f"missing required field: '{field}'"
        return True, "ok"
