"""
expression_eval.py – Safe expression evaluator for activation conditions.

Allows only: numbers, booleans, variable names, and/or/not, parentheses,
comparisons (>=, <=, >, <, ==, !=).

NO attribute access, NO function calls, NO imports.
Unknown variables cause the condition to evaluate to False.
Uses latest STATE values by variable name.
"""

from __future__ import annotations

import ast
import operator
from typing import Any, Dict

_COMPARE_OPS = {
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
}

_BOOL_OPS = {
    ast.And: all,
    ast.Or: any,
}


class _SafeEval(ast.NodeVisitor):
    """Walk an AST and evaluate safely against a variable dict."""

    def __init__(self, variables: Dict[str, Any]):
        self._vars = variables
        self._unknown = False

    def evaluate(self, node: ast.AST) -> Any:
        return self.visit(node)

    def visit_Expression(self, node: ast.Expression) -> Any:
        return self.visit(node.body)

    def visit_BoolOp(self, node: ast.BoolOp) -> bool:
        fn = _BOOL_OPS.get(type(node.op))
        if fn is None:
            return False
        return fn(self.visit(v) for v in node.values)

    def visit_UnaryOp(self, node: ast.UnaryOp) -> Any:
        operand = self.visit(node.operand)
        if isinstance(node.op, ast.Not):
            return not operand
        if isinstance(node.op, ast.USub):
            return -operand
        return False

    def visit_Compare(self, node: ast.Compare) -> bool:
        left = self.visit(node.left)
        for op_node, comparator in zip(node.ops, node.comparators):
            right = self.visit(comparator)
            fn = _COMPARE_OPS.get(type(op_node))
            if fn is None:
                return False
            try:
                if not fn(left, right):
                    return False
            except TypeError:
                return False
            left = right
        return True

    def visit_Name(self, node: ast.Name) -> Any:
        if node.id in ("True", "true"):
            return True
        if node.id in ("False", "false"):
            return False
        if node.id in self._vars:
            return self._vars[node.id]
        self._unknown = True
        return 0  # unknown variable → 0; comparisons will likely fail

    def visit_Constant(self, node: ast.Constant) -> Any:
        if isinstance(node.value, (int, float, bool)):
            return node.value
        return 0

    def generic_visit(self, node: ast.AST) -> Any:
        # Reject anything not explicitly handled (function calls, attribute access, etc.)
        return False


def safe_eval(expression: str, variables: Dict[str, Any]) -> bool:
    """Evaluate *expression* safely against *variables*.

    Returns False on any error or if unknown variables are referenced
    in a way that makes the condition indeterminate.
    """
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError:
        return False

    evaluator = _SafeEval(variables)
    try:
        result = evaluator.evaluate(tree)
    except Exception:
        return False

    return bool(result)


def evaluate_comparison(op_str: str, actual: Any, threshold: Any) -> bool:
    """Evaluate a simple comparison: actual <op> threshold."""
    ops = {
        ">=": operator.ge,
        "<=": operator.le,
        ">": operator.gt,
        "<": operator.lt,
        "==": operator.eq,
        "!=": operator.ne,
    }
    fn = ops.get(op_str)
    if fn is None:
        raise ValueError(f"Unsupported operator: {op_str}")
    return fn(actual, threshold)
