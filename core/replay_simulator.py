# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
Implements the Replay Simulator layer to generate dry-run plans for workflows.
"""

import json


def generate_replay_plan(sequence_or_macro):
    """Generate a replay plan for a given sequence or macro."""
    return {
        "steps": sequence_or_macro.get("steps", []),
        "expected_outputs": sequence_or_macro.get("expected_outputs", []),
        "verification_checks": sequence_or_macro.get("verification_checks", []),
        "abort_conditions": sequence_or_macro.get("abort_conditions", []),
        "estimated_time": sequence_or_macro.get("estimated_time", "unknown"),
    }
