from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from swarmz_server import app


def _mock_api_response(path: str) -> dict:
    if path.endswith("/health"):
        return {"status": "healthy", "active_missions": 0, "max_missions": 5, "pattern_counters": 0}
    if "/v1/missions/list" in path:
        return {"missions": []}
    if "/v1/addons/patches" in path:
        return {"patches": []}
    if "/v1/addons/budget" in path:
        return {"spent": 0, "hard_cap": 100, "reserved": 0}
    if "/v1/addons/quarantine" in path:
        return {"quarantined": False}
    if "/v1/addons/replay" in path:
        return {"ok": True, "events": []}
    return {"ok": True}


@pytest.mark.parametrize("route", ["/", "/console"])
def test_dashboard_browser_smoke_clicks(route: str) -> None:
    playwright = pytest.importorskip("playwright.sync_api")

    with TestClient(app) as client:
        response = client.get(route)
        assert response.status_code == 200
        html = response.text

    html = html.replace("<head>", "<head><base href=\"http://swarmz.local/\">", 1)

    page_errors: list[str] = []

    def route_handler(route) -> None:
        url = route.request.url
        if url.endswith("/nexusmon_console.js"):
            route.fulfill(
                status=200,
                body=(
                    "window.NexusmonConsole = {"
                    "connectWebSocket: function(){return true;},"
                    "init: function(){"
                    "return { mount:function(){return true;}, dispose:function(){return true;}, "
                    "sendPrompt:function(){return true;}, appendSystemMessage:function(){return true;} };"
                    "}"
                    "};"
                ),
                headers={"content-type": "application/javascript"},
            )
            return

        payload = _mock_api_response(url)
        route.fulfill(status=200, body=json.dumps(payload), headers={"content-type": "application/json"})

    with playwright.sync_playwright() as play:
        try:
            browser = play.chromium.launch(headless=True)
        except Exception as exc:  # pragma: no cover
            pytest.skip(f"Chromium unavailable for smoke test: {exc}")

        context = browser.new_context()
        page = context.new_page()
        page.on("pageerror", lambda exc: page_errors.append(str(exc)))
        page.route("http://swarmz.local/**", route_handler)
        page.add_init_script("window.open = () => null;")

        page.set_content(html)
        page.wait_for_selector("#bottom-bar")

        page.get_by_role("button", name="Research").click()
        page.get_by_role("button", name="Status").click()
        page.get_by_role("button", name="Swarm").click()

        assert page.locator("#bottom-bar .chip").count() >= 6
        assert not page_errors

        context.close()
        browser.close()
