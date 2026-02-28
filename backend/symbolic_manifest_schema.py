from __future__ import annotations

from typing import Any, Dict

from backend.symbolic_types import ALLOWED_SYMBOLIC_HOOKS

REQUIRED_MANIFEST_FIELDS: tuple[str, ...] = (
    "id",
    "name",
    "origin",
    "symbolic_role",
    "domains",
    "entities",
    "correspondences",
    "geometry",
    "runtime_hooks",
    "cockpit_modes",
    "operator_approval_required",
)


class SymbolicManifestValidationError(ValueError):
    """Raised when a symbolic manifest does not match the canonical pattern."""


def _require_dict(value: Any, field: str) -> Dict[str, Any]:
    if not isinstance(value, dict):
        raise SymbolicManifestValidationError(f"{field} must be an object")
    return value


def _require_list(value: Any, field: str) -> list[Any]:
    if not isinstance(value, list):
        raise SymbolicManifestValidationError(f"{field} must be a list")
    return value


def validate_manifest(manifest: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate a symbolic manifest against the universal schema contract.
    Returns the manifest unchanged if valid, raises on error.
    """
    missing = [field for field in REQUIRED_MANIFEST_FIELDS if field not in manifest]
    if missing:
        raise SymbolicManifestValidationError(
            f"missing required field(s): {', '.join(missing)}"
        )

    for str_field in ("id", "name", "origin", "symbolic_role"):
        value = manifest.get(str_field)
        if not isinstance(value, str) or not value.strip():
            raise SymbolicManifestValidationError(
                f"{str_field} must be a non-empty string"
            )

    _require_list(manifest.get("domains"), "domains")
    _require_list(manifest.get("entities"), "entities")
    _require_dict(manifest.get("correspondences"), "correspondences")

    geometry = _require_dict(manifest.get("geometry"), "geometry")
    # Accept either explicit points/lines arrays or an empty geometry object.
    # Normalize missing keys to preserve deterministic downstream handling.
    if "points" not in geometry:
        geometry["points"] = []
    if "lines" not in geometry:
        geometry["lines"] = []
    _require_list(geometry.get("points"), "geometry.points")
    _require_list(geometry.get("lines"), "geometry.lines")

    runtime_hooks = _require_dict(manifest.get("runtime_hooks"), "runtime_hooks")
    for hook in ALLOWED_SYMBOLIC_HOOKS:
        if hook not in runtime_hooks:
            raise SymbolicManifestValidationError(
                f"runtime_hooks missing required hook flag: {hook}"
            )
        if not isinstance(runtime_hooks[hook], bool):
            raise SymbolicManifestValidationError(
                f"runtime_hooks.{hook} must be a boolean"
            )

    _require_list(manifest.get("cockpit_modes"), "cockpit_modes")

    if manifest.get("operator_approval_required") is not True:
        raise SymbolicManifestValidationError(
            "operator_approval_required must be true"
        )

    return manifest
