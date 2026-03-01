from __future__ import annotations

from typing import Any, Dict, Final

ALLOWED_SYMBOLIC_HOOKS: Final[tuple[str, ...]] = (
    "on_invoke",
    "on_consult",
    "on_symbolic_interpretation",
    "on_generate_geometry",
    "on_trigger_anomaly",
    "on_resolve_correspondence",
    "on_render_altar_mode",
    "on_simulate_branch",
)


def framed_symbolic_response(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Attach the canonical non-literal symbolic framing contract to all runtime output.
    """
    return {
        **payload,
        "symbolic_only": True,
        "non_supernatural": True,
        "framing": "symbolic_narrative_interpretation",
    }
