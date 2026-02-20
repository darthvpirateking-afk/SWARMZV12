import importlib
from pathlib import Path


def _set_isolated_registry(monkeypatch, tmp_path):
    module = importlib.import_module("swarmz_runtime.api.fusion_routes")
    from swarmz_runtime.core.fusion_registry import FusionRegistry

    registry = FusionRegistry(Path(tmp_path))
    monkeypatch.setattr(module, "_registry", registry)


def test_fusion_register_list_and_verify(client, monkeypatch, tmp_path):
    _set_isolated_registry(monkeypatch, tmp_path)

    first = client.post(
        "/v1/fusion/register",
        json={
            "title": "Prime organism directive",
            "owner": "regan",
            "source": "operator_input",
            "summary": "Build SWARMZ PRIME first with governed evolution.",
            "tags": ["prime", "governance"],
            "linked_docs": ["docs/SWARMZ_DUAL_MODE_CHARTER.md"],
        },
    )
    assert first.status_code == 200
    assert first.json()["ok"] is True

    second = client.post(
        "/v1/fusion/register",
        json={
            "title": "Federation expansion",
            "owner": "regan",
            "source": "operator_input",
            "summary": "Add federation manager with sovereign organism lifecycle.",
            "tags": ["federation"],
            "linked_docs": ["docs/SWARMZ_DUAL_MODE_CHARTER.md"],
        },
    )
    assert second.status_code == 200

    rows = client.get("/v1/fusion/registry")
    assert rows.status_code == 200
    assert rows.json()["count"] == 2

    verify = client.get("/v1/fusion/verify")
    assert verify.status_code == 200
    assert verify.json()["valid"] is True

    summary = client.get("/v1/fusion/summary")
    assert summary.status_code == 200
    payload = summary.json()
    assert payload["entries"] == 2
    assert payload["owners"]["regan"] == 2
