from fastapi.testclient import TestClient

from server import app


def test_openapi_operation_ids_for_dashboard_and_runtime_routes():
    with TestClient(app) as client:
        openapi_path = app.openapi_url or "/openapi.json"
        response = client.get(openapi_path)
        if response.status_code == 404 and openapi_path != "/openapi.json":
            response = client.get("/openapi.json")

    assert response.status_code == 200
    spec = response.json()
    paths = spec.get("paths", {})

    manifest_get = paths.get("/pwa/manifest.json", {}).get("get", {})
    assert manifest_get.get("operationId") == "dashboard_pwa_manifest_get"

    runtime_scoreboard_get = paths.get("/v1/runtime/scoreboard", {}).get("get", {})
    assert (
        runtime_scoreboard_get.get("operationId") == "runtime_endpoints_scoreboard_get"
    )
