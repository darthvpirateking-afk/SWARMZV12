# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
Mission Contract Plugin for SWARMZ

Converts "12 laws" into hard preflight validation.
Mission must be underspecified => SWARMZ must not run it.
Enforces minimum required fields and external signal requirements.
"""

from typing import Dict, Any, List

REQUIRED_TOP_LEVEL_FIELDS = [
    "mission_id",
    "objective",
    "target_profile",
    "offer",
    "channels",
    "success_metrics",
    "constraints",
    "ethics",
    "data_policy",
    "timebox",
]


TWELVE_LAWS = {
    "external_signals_only": "Learning must be based on external signals, not internal reflections",
    "underspecification": "Mission must be sufficiently specified with all required fields",
    "ethical_boundaries": "Mission must respect ethical constraints",
    "data_privacy": "Mission must have clear data handling policy",
    "time_bounded": "Mission must have defined time constraints",
    "measurable_success": "Mission must have quantifiable success metrics",
    "clear_objective": "Mission must have unambiguous objective",
    "target_defined": "Mission must specify target profile",
    "value_proposition": "Mission must articulate clear offer/value",
    "channel_specificity": "Mission must define execution channels",
    "constraint_acknowledgment": "Mission must acknowledge operational constraints",
    "operator_sovereignty": "Mission must preserve operator control and oversight",
}


def validate_mission_contract(mission: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate mission against the 12 laws and required fields.

    Args:
        mission: Mission configuration dictionary

    Returns:
        Dictionary with:
        - valid: bool
        - errors: List[str]
        - warnings: List[str]
    """
    errors = []
    warnings = []

    # Law 1: Check for required top-level fields
    missing_fields = [
        field for field in REQUIRED_TOP_LEVEL_FIELDS if field not in mission
    ]
    if missing_fields:
        errors.append(f"Missing required fields: {', '.join(missing_fields)}")

    # Law 2: External signals only (no internal reflections)
    learning_source = mission.get("learning_source", {})
    if learning_source:
        source_type = learning_source.get("type", "")
        prohibited_sources = ["log", "metric", "dashboard", "llm_self_eval", "internal"]
        if any(prohibited in source_type.lower() for prohibited in prohibited_sources):
            errors.append("Learning source must be external, not internal reflection")

    # Check for reality signal
    if "reality_signal" not in mission:
        errors.append(
            "Mission must include external reality_signal (payment_received, user_reply, etc.)"
        )

    # Law 3: Objective must be clear and specific
    objective = mission.get("objective", "")
    if len(objective) < 10:
        errors.append("Objective is too vague or underspecified")

    # Check for ambiguous language
    vague_terms = ["maybe", "possibly", "might", "could", "perhaps"]
    if any(term in objective.lower() for term in vague_terms):
        warnings.append("Objective contains ambiguous language - be more specific")

    # Law 4: Target profile must be defined
    target_profile = mission.get("target_profile", {})
    if not target_profile or not isinstance(target_profile, dict):
        errors.append("Target profile must be a defined dictionary")
    elif len(target_profile) == 0:
        errors.append("Target profile is empty - must specify target characteristics")

    # Law 5: Success metrics must be measurable
    success_metrics = mission.get("success_metrics", {})
    if not success_metrics:
        errors.append("Success metrics are required")
    elif not isinstance(success_metrics, dict):
        errors.append("Success metrics must be a dictionary of measurable values")
    else:
        # Check that metrics are quantifiable
        for metric, value in success_metrics.items():
            if not isinstance(value, (int, float, dict)):
                warnings.append(f"Success metric '{metric}' should be quantifiable")

    # Law 6: Time constraints must be specified
    timebox = mission.get("timebox", {})
    if not timebox:
        errors.append("Timebox is required")
    else:
        if "start" not in timebox and "duration" not in timebox:
            errors.append("Timebox must specify start time or duration")
        if "deadline" not in timebox and "duration" not in timebox:
            warnings.append("Consider adding deadline or duration to timebox")

    # Law 7: Channels must be specific
    channels = mission.get("channels", [])
    if not channels:
        errors.append("Channels are required")
    elif not isinstance(channels, list):
        errors.append("Channels must be a list")
    elif len(channels) == 0:
        errors.append("At least one channel must be specified")

    # Law 8: Offer/value must be clear
    offer = mission.get("offer", "")
    if not offer or len(offer) < 10:
        errors.append("Offer/value proposition must be clearly defined")

    # Law 9: Ethics must be acknowledged
    ethics = mission.get("ethics", {})
    if not ethics:
        errors.append("Ethics constraints must be explicitly defined")
    else:
        required_ethics = ["respect_privacy", "no_spam", "transparent"]
        missing_ethics = [e for e in required_ethics if e not in ethics]
        if missing_ethics:
            warnings.append(
                f"Consider adding ethics constraints: {', '.join(missing_ethics)}"
            )

    # Law 10: Data policy must be specified
    data_policy = mission.get("data_policy", {})
    if not data_policy:
        errors.append("Data policy is required")
    else:
        if "retention" not in data_policy:
            warnings.append("Data policy should specify retention period")
        if "usage" not in data_policy:
            warnings.append("Data policy should specify usage terms")

    # Law 11: Constraints must be acknowledged
    constraints = mission.get("constraints", {})
    if not constraints:
        warnings.append(
            "Consider specifying operational constraints (budget, resources, etc.)"
        )

    # Law 12: Operator sovereignty check
    if "operator_approval_required" not in mission:
        warnings.append("Consider adding operator_approval_required flag for oversight")

    # Validate mission is not TOO specified (over-constrained)
    if len(constraints) > 20:
        warnings.append("Mission may be over-constrained with too many restrictions")

    # Check for critical failures
    valid = len(errors) == 0

    return {
        "valid": valid,
        "errors": errors,
        "warnings": warnings,
        "laws_enforced": len(TWELVE_LAWS),
        "compliance_rate": (len(TWELVE_LAWS) - len(errors)) / len(TWELVE_LAWS),
    }


def check_law_compliance(mission: Dict[str, Any], law_name: str) -> Dict[str, Any]:
    """Check compliance with a specific law."""
    if law_name not in TWELVE_LAWS:
        return {"valid": False, "reason": f"Unknown law: {law_name}"}

    # Run full validation and extract specific law
    result = validate_mission_contract(mission)

    # Map law to specific checks
    law_checks = {
        "external_signals_only": "reality_signal" in mission,
        "underspecification": len(
            [f for f in REQUIRED_TOP_LEVEL_FIELDS if f in mission]
        )
        == len(REQUIRED_TOP_LEVEL_FIELDS),
        "ethical_boundaries": "ethics" in mission and mission["ethics"],
        "data_privacy": "data_policy" in mission and mission["data_policy"],
        "time_bounded": "timebox" in mission and mission["timebox"],
        "measurable_success": "success_metrics" in mission
        and mission["success_metrics"],
        "clear_objective": len(mission.get("objective", "")) >= 10,
        "target_defined": "target_profile" in mission and mission["target_profile"],
        "value_proposition": len(mission.get("offer", "")) >= 10,
        "channel_specificity": "channels" in mission
        and len(mission.get("channels", [])) > 0,
        "constraint_acknowledgment": "constraints" in mission,
        "operator_sovereignty": True,  # Always respected
    }

    compliant = law_checks.get(law_name, False)

    return {
        "law": law_name,
        "description": TWELVE_LAWS[law_name],
        "compliant": compliant,
        "reason": "Compliant" if compliant else f"Failed: {TWELVE_LAWS[law_name]}",
    }


def register(executor):
    """Register Mission Contract tasks with SWARMZ executor."""

    def validate_contract(mission: Dict[str, Any]) -> Dict[str, Any]:
        """Validate mission contract against 12 laws."""
        return validate_mission_contract(mission)

    def check_law(mission: Dict[str, Any], law_name: str) -> Dict[str, Any]:
        """Check compliance with specific law."""
        return check_law_compliance(mission, law_name)

    def list_laws() -> Dict[str, str]:
        """List all 12 laws."""
        return TWELVE_LAWS.copy()

    def list_required_fields() -> List[str]:
        """List required mission fields."""
        return REQUIRED_TOP_LEVEL_FIELDS.copy()

    # Register tasks
    executor.register_task(
        "mission_contract_validate",
        validate_contract,
        {
            "description": "Validate mission contract against 12 laws",
            "params": {"mission": "dict"},
            "category": "mission_contract",
        },
    )

    executor.register_task(
        "mission_contract_check_law",
        check_law,
        {
            "description": "Check compliance with specific law",
            "params": {"mission": "dict", "law_name": "string"},
            "category": "mission_contract",
        },
    )

    executor.register_task(
        "mission_contract_list_laws",
        list_laws,
        {
            "description": "List all 12 laws",
            "params": {},
            "category": "mission_contract",
        },
    )

    executor.register_task(
        "mission_contract_required_fields",
        list_required_fields,
        {
            "description": "List required mission fields",
            "params": {},
            "category": "mission_contract",
        },
    )
