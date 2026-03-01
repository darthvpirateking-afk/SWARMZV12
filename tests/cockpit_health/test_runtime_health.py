from __future__ import annotations

from fastapi.testclient import TestClient

from swarmz_server import app

REQUIRED_FIELDS = {
    "manifestsTotal",
    "manifestsUnregistered",
    "hooksMissing",
    "cockpitModesTotal",
    "cockpitModesBroken",
    "testsTotal",
    "testsFailed",
    "observatorySizeMB",
    "lastDiaryWriteISO",
    "lastSchedulerRunISO",
    "legacyArtifactsFound",
}


def test_runtime_health_contains_required_fields() -> None:
    with TestClient(app) as client:
        resp = client.get("/v1/runtime/health")
    assert resp.status_code == 200
    payload = resp.json()
    assert REQUIRED_FIELDS.issubset(payload.keys())
