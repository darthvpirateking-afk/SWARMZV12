import importlib
from pathlib import Path


from swarmz_runtime.core.fusion_registry import FusionRegistry
from swarmz_runtime.core.operator_ecosystem import OperatorEcosystem


def _set_isolated_primal_runtime(monkeypatch, tmp_path):
    primal_routes = importlib.import_module("swarmz_runtime.api.primal_routes")
    ecosystem_routes = importlib.import_module("swarmz_runtime.api.operator_ecosystem_routes")
    fusion_routes = importlib.import_module("swarmz_runtime.api.fusion_routes")

    eco = OperatorEcosystem(Path(tmp_path))
    registry = FusionRegistry(Path(tmp_path))

    monkeypatch.setattr(primal_routes, "_ROOT_DIR", Path(tmp_path))
    monkeypatch.setattr(primal_routes, "_DOCTRINE_PATH", Path(tmp_path) / "config" / "doctrine_primal_block.json")
    monkeypatch.setattr(primal_routes, "_STATE_SLATE_PATH", Path(tmp_path) / "config" / "primal_state_slate.json")
    monkeypatch.setattr(primal_routes, "_ecosystem", eco)
    monkeypatch.setattr(primal_routes, "_fusion_registry", registry)

    monkeypatch.setattr(ecosystem_routes, "_ecosystem", eco)
    monkeypatch.setattr(fusion_routes, "_registry", registry)


def test_prime_state_endpoint_returns_primal_slate(client, monkeypatch, tmp_path):
    _set_isolated_primal_runtime(monkeypatch, tmp_path)

    state = client.get("/v1/operator-os/prime-state")
    assert state.status_code == 200

    payload = state.json()
    assert "SYSTEM_STATUS" in payload
    assert "SYSTEMS" in payload
    assert "CHANNELS" in payload


def test_riftwalk_trace_and_sigilstack_registry(client, monkeypatch, tmp_path):
    _set_isolated_primal_runtime(monkeypatch, tmp_path)

    event = client.post(
        "/v1/operator-os/timeline/event",
        json={
            "event_type": "mission_started",
            "domain": "missions",
            "risk": "low",
            "money_impact_cents": 0,
            "details": {"agent": "planner", "mission_id": "m-seed-1"},
        },
    )
    assert event.status_code == 200

    mission = client.post(
        "/v1/operator-os/missions/upsert",
        json={
            "mission_id": "m-seed-1",
            "mission_type": "seedrun",
            "status": "running",
            "risk_level": "low",
            "budget_cents": 100,
            "policy_profile": "default",
            "agents": ["planner"],
        },
    )
    assert mission.status_code == 200

    trace = client.get("/v1/riftwalk/trace?mission_id=m-seed-1")
    assert trace.status_code == 200
    trace_payload = trace.json()
    assert trace_payload["ok"] is True
    assert trace_payload["count"] == 1
    assert trace_payload["trace"][0]["mission_id"] == "m-seed-1"
    assert len(trace_payload["trace"][0]["steps"]) >= 1
    assert trace_payload["trace"][0]["result"]["status"] == "running"

    register = client.post(
        "/v1/fusion/register",
        json={
            "title": "Sigil attack module",
            "owner": "operator",
            "source": "combat_build",
            "summary": "Test sigil registration",
            "tags": ["tier:3", "attack"],
            "linked_docs": [],
        },
    )
    assert register.status_code == 200

    registry = client.get("/v1/sigilstack/registry")
    assert registry.status_code == 200
    registry_payload = registry.json()
    assert registry_payload["ok"] is True
    assert registry_payload["count"] == 1
    item = registry_payload["registry"][0]
    assert item["name"] == "Sigil attack module"
    assert item["tier"] == 3
    assert item["type"] == "ATTACK"
