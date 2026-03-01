from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODE_REGISTRY = ROOT / "cockpit" / "modes" / "mode_registry.json"
CANONICAL_REGISTRY = ROOT / "cockpit" / "modes" / "registry.json"

ALLOWED_HOOKS = {
    "on_invoke",
    "on_consult",
    "on_symbolic_interpretation",
    "on_generate_geometry",
    "on_trigger_anomaly",
    "on_resolve_correspondence",
    "on_render_altar_mode",
    "on_simulate_branch",
}


def test_mode_registry_file_and_fields() -> None:
    assert MODE_REGISTRY.exists()
    payload = json.loads(MODE_REGISTRY.read_text(encoding="utf-8-sig"))
    routes = payload.get("routes", [])
    assert isinstance(routes, list) and routes
    for route in routes:
        assert route["button_id"]
        assert route["mode_id"]
        assert route["hook"] in ALLOWED_HOOKS
        assert route["endpoint"].startswith("/")
        assert route["system_id"]


def test_mode_component_files_exist() -> None:
    payload = json.loads(MODE_REGISTRY.read_text(encoding="utf-8-sig"))
    for route in payload.get("routes", []):
        mode_file = ROOT / "cockpit" / "modes" / f"{route['mode_id']}.tsx"
        assert mode_file.exists(), f"missing mode component: {mode_file}"


def test_canonical_registry_references_existing_modes() -> None:
    assert CANONICAL_REGISTRY.exists()
    payload = json.loads(CANONICAL_REGISTRY.read_text(encoding="utf-8-sig"))
    modes = payload.get("modes", [])
    assert isinstance(modes, list) and modes
    for mode in modes:
        assert set(mode.keys()) == {"id", "path"}
        assert mode["id"]
        assert mode["path"].startswith("cockpit/modes/")
        assert mode["path"].endswith(".tsx")
        mode_file = ROOT / mode["path"]
        assert mode_file.exists(), f"registry path missing: {mode_file}"
        assert mode_file.stem == mode["id"]
