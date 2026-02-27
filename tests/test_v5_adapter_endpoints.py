from fastapi.testclient import TestClient

from swarmz_server import app


def test_firecrawl_health_endpoint_reports_availability():
    with TestClient(app) as client:
        response = client.get("/v1/intel/firecrawl/health")

        assert response.status_code == 200
        body = response.json()
        assert body.get("ok") is True
        assert body.get("endpoint") == "/v1/intel/firecrawl"
        assert "available" in body


def test_phase_pipeline_health_endpoint_reports_availability():
    with TestClient(app) as client:
        response = client.get("/v1/missions/phase/health")

        assert response.status_code == 200
        body = response.json()
        assert body.get("ok") is True
        assert body.get("endpoint") == "/v1/missions/phase/run"
        assert "available" in body


def test_v5_adapter_openapi_metadata_present():
    with TestClient(app) as client:
        response = client.get("/docs/openapi.json")

    assert response.status_code == 200
    spec = response.json()
    paths = spec.get("paths", {})

    firecrawl_post = paths.get("/v1/intel/firecrawl", {}).get("post", {})
    assert firecrawl_post.get("summary") == "Run firecrawl intelligence pipeline"
    assert firecrawl_post.get("tags") == ["Intel"]

    phase_post = paths.get("/v1/missions/phase/run", {}).get("post", {})
    assert phase_post.get("summary") == "Run mission phase pipeline"
    assert phase_post.get("tags") == ["Missions"]

    firecrawl_health_get = paths.get("/v1/intel/firecrawl/health", {}).get("get", {})
    assert firecrawl_health_get.get("summary") == "Check firecrawl adapter availability"

    phase_health_get = paths.get("/v1/missions/phase/health", {}).get("get", {})
    assert phase_health_get.get("summary") == "Check mission phase adapter availability"


def test_firecrawl_endpoint_runs_pipeline(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    with TestClient(app) as client:
        response = client.post(
            "/v1/intel/firecrawl",
            json={
                "mission_id": "m-http-1",
                "url": "https://example.local",
                "content": "token = ghp_abcdefghijklmnopqrstuvwxyz1234567890",
                "js_detected": True,
                "curiosity": 80,
                "creativity": 80,
                "patience": 80,
                "aggression": 40,
            },
        )

        assert response.status_code == 200
        body = response.json()
        assert body.get("ok") is True
        result = body.get("result", {})
        assert result.get("mission_id") == "m-http-1"
        assert "secret_findings" in result
        assert "archive" in result


def test_phase_pipeline_endpoint_guarantees_cleanup(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    with TestClient(app) as client:
        response = client.post(
            "/v1/missions/phase/run",
            json={
                "mission_id": "m-http-2",
                "autonomy": 80,
                "protectiveness": 80,
                "patience": 80,
                "fail": True,
            },
        )

        assert response.status_code == 200
        body = response.json()
        assert body.get("ok") is True
        result = body.get("result", {})
        assert result.get("status") == "FAILED"
        assert result.get("vpn_destroyed") is True
