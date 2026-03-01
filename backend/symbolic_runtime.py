from __future__ import annotations

from typing import Any, Dict

from backend.symbolic_types import ALLOWED_SYMBOLIC_HOOKS, framed_symbolic_response


def _ensure_hook_enabled(manifest: Dict[str, Any], hook: str) -> None:
    hooks = manifest.get("runtime_hooks", {})
    if hook not in ALLOWED_SYMBOLIC_HOOKS:
        raise ValueError(f"unsupported hook: {hook}")
    if not hooks.get(hook, False):
        raise ValueError(f"hook disabled in manifest: {hook}")


def dispatch_hook(
    hook: str,
    family: str,
    manifest: Dict[str, Any],
    payload: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Deterministic symbolic runtime dispatcher.
    Produces narrative metadata only; never performs literal or destructive actions.
    """
    _ensure_hook_enabled(manifest, hook)

    context = str(payload.get("context", "")).strip() or "no-context"
    focus = str(payload.get("focus", manifest.get("symbolic_role", "symbolic-role")))
    entities = manifest.get("entities", [])
    domains = manifest.get("domains", [])
    correspondences = manifest.get("correspondences", {})
    geometry = manifest.get("geometry", {})
    cockpit_modes = manifest.get("cockpit_modes", [])

    if hook == "on_generate_geometry":
        result = {
            "pattern": {
                "points": geometry.get("points", []),
                "lines": geometry.get("lines", []),
            },
            "summary": f"Generated symbolic geometry for {manifest['name']}.",
        }
    elif hook == "on_trigger_anomaly":
        result = {
            "anomaly_frame": f"{manifest['name']} treats this as a symbolic anomaly motif.",
            "context": context,
            "summary": "Anomaly framing produced without predictive claims.",
        }
    elif hook == "on_resolve_correspondence":
        result = {
            "correspondences": correspondences,
            "summary": f"Resolved correspondences for focus={focus}.",
        }
    elif hook == "on_render_altar_mode":
        result = {
            "mode": cockpit_modes[0] if cockpit_modes else "default-symbolic-mode",
            "summary": "Rendered a symbolic UI theme profile.",
        }
    elif hook == "on_simulate_branch":
        result = {
            "branch": {
                "name": f"{manifest['id']}-branch",
                "divergence": f"Symbolic what-if branch for context={context}",
            },
            "summary": "Simulated symbolic branch narrative.",
        }
    elif hook == "on_symbolic_interpretation":
        result = {
            "interpretation": (
                f"{manifest['name']} interprets context='{context}' "
                f"through domains={domains}."
            ),
            "summary": "Generated symbolic interpretation.",
        }
    elif hook == "on_consult":
        result = {
            "guidance": (
                f"Symbolic consult from {manifest['name']}: "
                f"focus on role={manifest['symbolic_role']}."
            ),
            "summary": "Produced metaphorical consult guidance.",
        }
    else:  # on_invoke
        result = {
            "invocation": f"Activated symbolic profile {manifest['name']} for focus={focus}.",
            "entities": entities,
            "summary": "Invocation recorded as symbolic runtime action.",
        }

    return framed_symbolic_response(
        {
            "hook": hook,
            "family": family,
            "manifest_id": manifest.get("id"),
            "result": result,
        }
    )

