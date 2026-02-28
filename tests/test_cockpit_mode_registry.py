from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODE_REGISTRY = ROOT / "cockpit" / "modes" / "mode_registry.json"
COCKPIT_HTML = ROOT / "ui" / "nexusmon-cockpit.html"

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


def test_cockpit_buttons_match_mode_routes() -> None:
    html = COCKPIT_HTML.read_text(encoding="utf-8-sig")
    payload = json.loads(MODE_REGISTRY.read_text(encoding="utf-8-sig"))
    for route in payload.get("routes", []):
        assert f'id="{route["button_id"]}"' in html
