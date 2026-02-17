# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
Implements the One Throat Wrapper layer to centralize action handling.
"""

from core.enforcement_mode import handle_violation
from core.reality_classifier import handle_action

def one_throat_handler(action_name, action_func, *args, **kwargs):
    """
    Centralized handler for all actions.
    """
    # Classify the action
    action_result = handle_action(action_name)

    if not action_result["allow"]:
        # Handle enforcement if action is blocked
        return handle_violation(action_name, action_result["reason"])

    # Execute the action if allowed
    try:
        result = action_func(*args, **kwargs)
        return {"success": True, "result": result}
    except Exception as e:
        return {"success": False, "error": str(e)}
