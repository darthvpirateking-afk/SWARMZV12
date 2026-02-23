from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class BrowserReconResult:
    url: str
    dom_snapshot: str
    network_calls: list[dict[str, Any]] = field(default_factory=list)
    ws_endpoints: list[str] = field(default_factory=list)
    js_routes: list[str] = field(default_factory=list)
    forms: list[dict[str, Any]] = field(default_factory=list)
    auth_flow: dict[str, Any] = field(default_factory=dict)
    cookies: list[dict[str, Any]] = field(default_factory=list)
    screenshots: list[str] = field(default_factory=list)


def get_browser_recon_config(
    curiosity: int, creativity: int, patience: int
) -> dict[str, Any]:
    return {
        "enabled": curiosity >= 45,
        "browser": "chromium",
        "headless": True,
        "intercept_network": curiosity >= 55,
        "extract_js_routes": creativity >= 60,
        "detect_auth_flows": creativity >= 50,
        "capture_websockets": curiosity >= 65,
        "screenshot_on_each_page": patience >= 55,
        "max_pages": int((patience / 100) * 100),
        "js_timeout_ms": 3000 + int((patience / 100) * 7000),
        "archive_dom_snapshots": patience >= 40,
        "multi_browser_test": creativity >= 75,
    }


def extract_attack_surface(
    result: BrowserReconResult, aggression: int
) -> dict[str, Any]:
    surface = {
        "endpoints": [
            str(call.get("url", "")) for call in result.network_calls if call.get("url")
        ],
        "ws_targets": list(result.ws_endpoints),
        "forms": list(result.forms),
        "auth_bypass_candidates": [],
    }

    if aggression >= 30:
        surface["auth_bypass_candidates"] = [
            form for form in result.forms if not form.get("csrf_token")
        ]

    return surface


def should_run_browser_recon(
    js_detected: bool, curiosity: int, creativity: int, patience: int
) -> bool:
    cfg = get_browser_recon_config(curiosity, creativity, patience)
    return bool(js_detected and cfg["enabled"] and cfg["headless"])
