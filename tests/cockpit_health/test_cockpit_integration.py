from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from swarmz_server import app

ROOT = Path(__file__).resolve().parents[2]
MODE_REGISTRY = ROOT / "cockpit" / "modes" / "registry.json"
ASSET_MAP = ROOT / "cockpit" / "assets" / "asset_map.json"


def test_cockpit_integration_surface_loads_without_404s() -> None:
    mode_payload = json.loads(MODE_REGISTRY.read_text(encoding="utf-8-sig"))
    asset_payload = json.loads(ASSET_MAP.read_text(encoding="utf-8-sig"))
    modes = mode_payload.get("modes", [])

    with TestClient(app) as client:
        root_resp = client.get("/cockpit/")
        assert root_resp.status_code == 200

        bridge_resp = client.get("/v1/canonical/agents")
        assert bridge_resp.status_code == 200

        reg_resp = client.get("/cockpit/modes/registry.json")
        assert reg_resp.status_code == 200

        asset_resp = client.get("/cockpit/assets/asset_map.json")
        assert asset_resp.status_code == 200

        for mode in modes:
            rel = str(mode["path"]).replace("cockpit/", "", 1)
            resp = client.get(f"/cockpit/{rel}")
            assert resp.status_code != 404, mode["path"]
            assert resp.status_code == 200, mode["path"]

        for key in ("js_bundles", "css_bundles", "images", "mode_components"):
            for path in asset_payload.get(key, []):
                rel = str(path).lstrip("/")
                assert (ROOT / rel).exists(), path
