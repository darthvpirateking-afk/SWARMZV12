# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
expression_eval.py â€“ Safe expression evaluator for the control plane.

Evaluates simple comparison expressions against state variables without
using ``eval()`` or ``exec()``.
"""

import operator

_OPS = {
    ">=": operator.ge,
    "<=": operator.le,
    ">": operator.gt,
    "<": operator.lt,
    "==": operator.eq,
    "!=": operator.ne,
}


def evaluate(op_str: str, actual, threshold) -> bool:
    """Return True when *actual* satisfies the comparison *op_str* against *threshold*."""
    fn = _OPS.get(op_str)
    if fn is None:
        raise ValueError(f"Unsupported operator: {op_str}")
    return fn(actual, threshold)

