# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
Reality Gate Plugin for SWARMZ

Ensures SWARMZ only learns/mutates/scales based on EXTERNAL signals.
Internal logs, LLM self-evaluations, and dashboards are reflections (non-authoritative).

External signals:
- payment_received
- user_reply
- external_click
- account_created
- api_conversion
- manual_confirmation
"""

from typing import Dict, Any


# Valid external signals
VALID_EXTERNAL_SIGNALS = {
    "payment_received": "Payment transaction confirmed",
    "user_reply": "User provided explicit feedback/response",
    "external_click": "User clicked on external link/action",
    "account_created": "New account registered in system",
    "api_conversion": "External API confirmed conversion",
    "manual_confirmation": "Human operator manually confirmed action"
}


def reality_gate(mission: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate that a mission is grounded in external reality signals.
    
    Args:
        mission: Mission configuration dictionary
    
    Returns:
        Dictionary with:
        - valid: bool - whether mission passes reality gate
        - reason: str - explanation of decision
        - signal: str or None - detected external signal if valid
    """
    # Check if mission has reality signal
    signal = mission.get("reality_signal")
    
    if not signal:
        return {
            "valid": False,
            "reason": "Mission lacks external reality signal. SWARMZ must not operate on internal reflections.",
            "signal": None
        }
    
    # Validate signal is from approved external sources
    if signal not in VALID_EXTERNAL_SIGNALS:
        return {
            "valid": False,
            "reason": f"Signal '{signal}' is not a recognized external signal. "
                     f"Valid signals: {', '.join(VALID_EXTERNAL_SIGNALS.keys())}",
            "signal": None
        }
    
    # Check for prohibited internal signals
    prohibited_patterns = [
        "self_eval", "internal_log", "dashboard", "metric", 
        "llm_output", "model_confidence", "prediction"
    ]
    
    signal_lower = signal.lower()
    for pattern in prohibited_patterns:
        if pattern in signal_lower:
            return {
                "valid": False,
                "reason": f"Signal contains prohibited internal pattern '{pattern}'. "
                         "SWARMZ must not learn from internal reflections.",
                "signal": None
            }
    
    # Validate signal has required metadata
    signal_data = mission.get("signal_data", {})
    
    required_fields = ["timestamp", "source", "verified"]
    missing_fields = [f for f in required_fields if f not in signal_data]
    
    if missing_fields:
        return {
            "valid": False,
            "reason": f"Signal metadata missing required fields: {', '.join(missing_fields)}",
            "signal": signal
        }
    
    # Check if signal is verified
    if not signal_data.get("verified"):
        return {
            "valid": False,
            "reason": "Signal is not verified. External signals must be verified before use.",
            "signal": signal
        }
    
    # All checks passed
    return {
        "valid": True,
        "reason": f"Mission validated with external signal: {VALID_EXTERNAL_SIGNALS[signal]}",
        "signal": signal
    }


def validate_learning_source(source: Dict[str, Any]) -> Dict[str, bool]:
    """
    Validate that a learning source is external, not internal reflection.
    
    Args:
        source: Learning source descriptor
    
    Returns:
        Dictionary with validation results
    """
    source_type = source.get("type", "")
    
    # Prohibited internal sources
    internal_sources = [
        "log", "metric", "dashboard", "llm_self_eval", 
        "model_output", "internal_analytics", "prediction"
    ]
    
    is_internal = any(internal in source_type.lower() for internal in internal_sources)
    
    if is_internal:
        return {
            "valid": False,
            "is_external": False,
            "reason": f"Source type '{source_type}' is an internal reflection. "
                     "Learning must be based on external signals only."
        }
    
    # Must have external verification
    if not source.get("external_verified"):
        return {
            "valid": False,
            "is_external": False,
            "reason": "Source lacks external verification flag"
        }
    
    return {
        "valid": True,
        "is_external": True,
        "reason": "Source is externally verified"
    }


def register(executor):
    """Register Reality Gate tasks with SWARMZ executor."""
    
    def check_reality_gate(mission: Dict[str, Any]) -> Dict[str, Any]:
        """Check if mission passes reality gate validation."""
        return reality_gate(mission)
    
    def validate_signal(signal_name: str, signal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a specific external signal."""
        mission = {
            "reality_signal": signal_name,
            "signal_data": signal_data
        }
        return reality_gate(mission)
    
    def list_valid_signals() -> Dict[str, str]:
        """List all valid external signals."""
        return VALID_EXTERNAL_SIGNALS.copy()
    
    def check_learning_source(source_type: str, external_verified: bool = False) -> Dict[str, Any]:
        """Check if a learning source is valid (external)."""
        source = {
            "type": source_type,
            "external_verified": external_verified
        }
        return validate_learning_source(source)
    
    # Register tasks
    executor.register_task("reality_gate_check", check_reality_gate, {
        "description": "Validate mission against reality gate (external signals only)",
        "params": {"mission": "dict"},
        "category": "reality_gate"
    })
    
    executor.register_task("reality_gate_validate_signal", validate_signal, {
        "description": "Validate a specific external signal",
        "params": {"signal_name": "string", "signal_data": "dict"},
        "category": "reality_gate"
    })
    
    executor.register_task("reality_gate_list_signals", list_valid_signals, {
        "description": "List all valid external signals",
        "params": {},
        "category": "reality_gate"
    })
    
    executor.register_task("reality_gate_check_learning_source", check_learning_source, {
        "description": "Check if learning source is external (not internal reflection)",
        "params": {"source_type": "string", "external_verified": "bool"},
        "category": "reality_gate"
    })

