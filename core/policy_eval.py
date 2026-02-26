"""Policy Evaluator (P0.1)

A stateless, deterministic scoring engine for all risky actions.

Primary principles:
- Pre-evaluated: Score before execution.
- Rule-bounded: Explicit policy constraints.
- Threshold: Trigger only above/below a cutoff.

Responsibilities:
- Ingest an action request (e.g., mission step, patchpack deployment).
- Score it against multiple dimensions (risk, cost, reversibility, etc.).
- Return a clear {admit|deny} decision with a reason.
- No side effects. This module does not *enforce* the policy, it only *evaluates* it.
  The caller (e.g., orchestrator, API route) is responsible for enforcement.
"""

from typing import Any, Dict, NamedTuple, List

# --------------------------------------------------------------------------
# Data Models
# --------------------------------------------------------------------------


class PolicyDecision(NamedTuple):
    """The output of a policy evaluation."""

    admit: bool
    score: float
    reasons: List[str]
    severity: str  # S1 (Low), S2 (Moderate), S3 (High), S4 (Critical)


class PolicyRule(NamedTuple):
    """A single rule to evaluate against an action."""

    name: str
    condition: str  # A simple expression to evaluate, e.g., "risk > 0.8"
    on_true: PolicyDecision


# --------------------------------------------------------------------------
# Default Rule Set
# --------------------------------------------------------------------------

# These rules provide a baseline for system safety. They can be augmented
# or overridden by a configuration loader.
DEFAULT_RULES: List[PolicyRule] = [
    # --- Critical (S4) ---
    PolicyRule(
        name="deny_high_risk_non_reversible",
        condition="context.get('risk_score', 0) > 0.9 and not context.get('is_reversible', False)",
        on_true=PolicyDecision(
            admit=False,
            score=1.0,
            reasons=["High-risk action is not reversible"],
            severity="S4",
        ),
    ),
    PolicyRule(
        name="deny_critical_impact_action",
        condition="'critical' in context.get('impact_tags', [])",
        on_true=PolicyDecision(
            admit=False,
            score=1.0,
            reasons=["Action has 'critical' impact tag"],
            severity="S4",
        ),
    ),
    # --- High (S3) ---
    PolicyRule(
        name="deny_excessive_cost",
        condition="context.get('cost_score', 0) > 0.95",
        on_true=PolicyDecision(
            admit=False,
            score=0.95,
            reasons=["Action cost exceeds 95% threshold"],
            severity="S3",
        ),
    ),
    PolicyRule(
        name="deny_unverified_source",
        condition="context.get('source_trust', 'untrusted') == 'untrusted'",
        on_true=PolicyDecision(
            admit=False,
            score=0.9,
            reasons=["Action source is untrusted"],
            severity="S3",
        ),
    ),
    # --- Moderate (S2) ---
    PolicyRule(
        name="warn_high_risk_reversible",
        condition="context.get('risk_score', 0) > 0.8",
        on_true=PolicyDecision(
            admit=True,
            score=0.8,
            reasons=["High-risk action, proceed with caution (reversible)"],
            severity="S2",
        ),
    ),
    PolicyRule(
        name="warn_moderate_cost",
        condition="context.get('cost_score', 0) > 0.7",
        on_true=PolicyDecision(
            admit=True, score=0.7, reasons=["Action has moderate cost"], severity="S2"
        ),
    ),
    # --- Low (S1) ---
    PolicyRule(
        name="default_allow",
        condition="True",
        on_true=PolicyDecision(
            admit=True, score=0.1, reasons=["Default policy: allow"], severity="S1"
        ),
    ),
]


# --------------------------------------------------------------------------
# Evaluation Logic
# --------------------------------------------------------------------------


def _evaluate_condition(condition: str, context: Dict[str, Any]) -> bool:
    """
    Safely evaluate a rule's condition string against the given context.
    This uses a restricted `eval()` to safely execute the condition.
    """
    if condition == "True":
        return True

    # The context provided to eval is a dictionary containing only 'context' and 'action'.
    # The __builtins__ are restricted to prevent access to unsafe functions.
    allowed_builtins = {
        "True": True,
        "False": False,
        "None": None,
        "len": len,
        "str": str,
        "int": int,
        "float": float,
        "list": list,
        "dict": dict,
        "in": lambda a, b: a in b,
        "not in": lambda a, b: a not in b,
    }

    try:
        # The 'action' key is added for backward compatibility with some rule formats.
        eval_context = {
            "context": context,
            "action": context,  # Allow rules to use 'action.get(...)'
            "__builtins__": allowed_builtins,
        }
        return bool(eval(condition, eval_context))
    except Exception:
        # If any part of evaluation fails, the condition is false.
        return False


def evaluate_action(
    action: Dict[str, Any],
    context: Dict[str, Any],
    rules: List[PolicyRule] = DEFAULT_RULES,
) -> PolicyDecision:
    """
    Evaluate an action against a set of policy rules.

    Args:
        action: A dictionary describing the action to be taken.
        context: A dictionary containing metadata about the action, such as
                 risk score, cost, reversibility, etc.
        rules: A list of PolicyRule tuples to evaluate against.

    Returns:
        A PolicyDecision tuple containing the outcome.
    """
    full_context = {**action, **context}

    for rule in rules:
        if _evaluate_condition(rule.condition, full_context):
            # First rule that matches wins.
            return rule.on_true

    # This should be unreachable if a "default_allow" rule exists.
    return PolicyDecision(
        admit=False,
        score=1.0,
        reasons=["Fell through all rules; default deny"],
        severity="S4",
    )
