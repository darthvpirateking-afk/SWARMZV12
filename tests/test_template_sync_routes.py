import importlib
from pathlib import Path


def _set_isolated_manager(monkeypatch, tmp_path):
    module = importlib.import_module("swarmz_runtime.api.template_sync_routes")
    from swarmz_runtime.core.template_sync import TemplateSyncManager

    manager = TemplateSyncManager(Path(tmp_path))
    monkeypatch.setattr(module, "_manager", manager)


def test_template_sync_config_and_allowlist(client, monkeypatch, tmp_path):
    _set_isolated_manager(monkeypatch, tmp_path)

    updated = client.post(
        "/v1/template-sync/config",
        json={
            "operator_id": "regan",
            "allowlist": ["https://github.com/open-source-org/"],
            "auto_sync": False,
            "sync_interval_hours": 12,
        },
    )
    assert updated.status_code == 200
    payload = updated.json()["config"]
    assert payload["operator_id"] == "regan"
    assert payload["sync_interval_hours"] == 12

    fetched = client.get("/v1/template-sync/config")
    assert fetched.status_code == 200
    assert fetched.json()["config"]["operator_id"] == "regan"


def test_template_sync_queue_requires_operator_binding(client, monkeypatch, tmp_path):
    _set_isolated_manager(monkeypatch, tmp_path)

    no_bind = client.post(
        "/v1/template-sync/queue",
        json={
            "operator_id": "regan",
            "source_url": "https://github.com/open-source-org/templates",
            "template_name": "starter",
            "dry_run": True,
        },
    )
    assert no_bind.status_code == 400

    client.post(
        "/v1/template-sync/config",
        json={
            "operator_id": "regan",
            "allowlist": ["https://github.com/open-source-org/"],
        },
    )

    bad_source = client.post(
        "/v1/template-sync/queue",
        json={
            "operator_id": "regan",
            "source_url": "https://evil.example.com/templates",
            "template_name": "starter",
            "dry_run": True,
        },
    )
    assert bad_source.status_code == 400

    ok = client.post(
        "/v1/template-sync/queue",
        json={
            "operator_id": "regan",
            "source_url": "https://github.com/open-source-org/templates",
            "template_name": "starter",
            "dry_run": True,
        },
    )
    assert ok.status_code == 200
    assert ok.json()["ok"] is True


def test_template_sync_template_link_and_jobs(client, monkeypatch, tmp_path):
    _set_isolated_manager(monkeypatch, tmp_path)

    client.post(
        "/v1/template-sync/config",
        json={
            "operator_id": "regan",
            "allowlist": ["https://github.com/open-source-org/"],
            "auto_sync": True,
        },
    )

    linked = client.post(
        "/v1/template-sync/queue",
        json={
            "operator_id": "regan",
            "source_url": "https://github.com/open-source-org/templates",
            "template_name": "ops-template",
            "dry_run": False,
        },
    )
    assert linked.status_code == 200
    assert "template" in linked.json()

    jobs = client.get("/v1/template-sync/jobs")
    assert jobs.status_code == 200
    assert jobs.json()["count"] >= 1

    templates = client.get("/v1/template-sync/templates")
    assert templates.status_code == 200
    assert templates.json()["count"] >= 1


def test_companion_bond_personalization(client):
    set_resp = client.post(
        "/v1/companion/bond",
        json={
            "operator_id": "regan",
            "tone": "loyal",
            "style": "focused",
            "focus": "operator_success",
        },
    )
    assert set_resp.status_code == 200
    assert set_resp.json()["ok"] is True

    get_resp = client.get("/v1/companion/bond")
    assert get_resp.status_code == 200
    bond = get_resp.json()["bond"]
    assert bond["operator_id"] == "regan"
    assert bond["style"] == "focused"
