from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from swarmz_server import app


@pytest.mark.parametrize("route", ["/", "/organism", "/console", "/cockpit/"])
def test_cockpit_routes_resolve_to_canonical_surface(route: str) -> None:
    with TestClient(app) as client:
        response = client.get(route, follow_redirects=True)

    assert response.status_code == 200
    assert 'id="app"' in response.text
    assert "NEXUSMON Hologram Cockpit" in response.text
    assert str(response.url).endswith("/cockpit/")
