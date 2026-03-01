"""Helper1 v0.2.0 validation engine API tests."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client() -> TestClient:
    try:
        from swarmz_server import app
    except Exception as exc:  # pragma: no cover
        pytest.skip(f"swarmz_server unavailable: {exc}")
    return TestClient(app)


def _operator_headers() -> dict[str, str]:
    return {"X-Operator-Approval": "true"}


def _helper_manifest_payload() -> dict:
    repo_root = Path(__file__).resolve().parent.parent
    payload = json.loads(
        (repo_root / "config" / "manifests" / "helper1.manifest.json").read_text(
            encoding="utf-8-sig"
        )
    )
    return payload


def test_helper1_legacy_query_compatibility(client: TestClient) -> None:
    res = client.post(
        "/v1/agents/helper1/run",
        json={"query": "hello from legacy"},
        headers=_operator_headers(),
    )
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert body["command"] == "echo"
    assert body["compatibility_mode"]["legacy_query"] is True
    assert body["result"]["echo"]["query"] == "hello from legacy"


def test_helper1_validate_manifest_success(client: TestClient) -> None:
    res = client.post(
        "/v1/agents/helper1/run",
        json={
            "command": "validate_manifest",
            "payload": {"manifest": _helper_manifest_payload()},
        },
        headers=_operator_headers(),
    )
    assert res.status_code == 200
    body = res.json()
    report = body["result"]
    assert body["command"] == "validate_manifest"
    assert report["valid"] is True
    assert isinstance(report["risk_score"], float)
    assert "errors" in report
    assert "warnings" in report
    assert "suggestions" in report
    assert "summary" in report


def test_helper1_validate_manifest_failure(client: TestClient) -> None:
    invalid_manifest = {"id": "broken", "version": "0.1.0"}
    res = client.post(
        "/v1/agents/helper1/run",
        json={"command": "validate_manifest", "payload": {"manifest": invalid_manifest}},
        headers=_operator_headers(),
    )
    assert res.status_code == 200
    body = res.json()
    report = body["result"]
    assert report["valid"] is False
    assert report["errors"]


def test_helper1_validate_proposal_dangerous_code(client: TestClient) -> None:
    proposal = {
        "manifest": _helper_manifest_payload(),
        "code_snippet": "def dangerous():\n    import os\n    return eval('1+1')\n",
    }
    res = client.post(
        "/v1/agents/helper1/run",
        json={"command": "validate_proposal", "payload": proposal},
        headers=_operator_headers(),
    )
    assert res.status_code == 200
    body = res.json()
    report = body["result"]
    assert report["approved_for_ritual"] is False
    assert report["risk_score"] >= 0.8
    assert report["errors"]


def test_helper1_status_and_capabilities_by_alias_and_full_id(client: TestClient) -> None:
    for agent_id in ("helper1", "helper1@0.2.0"):
        status = client.get(f"/v1/agents/{agent_id}/status")
        assert status.status_code == 200
        capabilities = client.get(f"/v1/agents/{agent_id}/capabilities")
        assert capabilities.status_code == 200


def test_canonical_agents_reflect_helper1_v020(client: TestClient) -> None:
    res = client.get("/v1/canonical/agents")
    assert res.status_code == 200
    payload = res.json()
    helper_entries = [a for a in payload.get("agents", []) if a.get("id") == "helper1"]
    assert helper_entries
    assert helper_entries[0].get("manifest") == "helper1@0.2.0"
