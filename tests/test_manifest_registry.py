"""ManifestRegistry unit tests."""
from __future__ import annotations

import json
from pathlib import Path

from core.agent_manifest import AgentManifest
from core.manifest_registry import ManifestRegistry


def _manifest(
    agent_id: str,
    capabilities: list[str],
    *,
    spawn_policy: str = "ephemeral",
    fallback_agent_id: str | None = None,
) -> dict[str, object]:
    error_modes: dict[str, object] = {
        "on_validation_failure": "reject",
        "on_dependency_missing": "defer",
        "on_runtime_exception": "fallback",
        "max_retries": 0,
    }
    if fallback_agent_id is not None:
        error_modes["fallback_agent_id"] = fallback_agent_id

    return {
        "id": agent_id,
        "version": "0.1.0",
        "capabilities": capabilities,
        "inputs": {"query": {"type": "string", "required": True}},
        "outputs": {"result": {"type": "object", "required": True}},
        "spawn_policy": spawn_policy,
        "constraints": {
            "max_memory_mb": 128,
            "max_cpu_percent": 10,
            "max_spawn_depth": 1,
            "network_access": False,
            "filesystem_access": "none",
            "allowed_capabilities": capabilities,
            "trust_level": 0.9,
        },
        "error_modes": error_modes,
    }


def test_register_and_query_by_capability() -> None:
    registry = ManifestRegistry()
    helper = AgentManifest.from_dict(_manifest("helper1", ["data.read", "agent.introspect"]))
    gate = AgentManifest.from_dict(_manifest("reality_gate", ["gate.evaluate", "data.read"]))

    registry.register(helper)
    registry.register(gate)

    assert len(registry) == 2
    assert registry.get("helper1") is helper
    assert {m.id for m in registry.query("data.read")} == {"helper1", "reality_gate"}
    assert registry.capabilities() == {"data.read", "agent.introspect", "gate.evaluate"}


def test_register_overwrite_updates_capability_index() -> None:
    registry = ManifestRegistry()
    v1 = AgentManifest.from_dict(_manifest("helper1", ["data.read"]))
    v2 = AgentManifest.from_dict(_manifest("helper1", ["mission.validate"]))

    registry.register(v1)
    registry.register(v2)

    assert len(registry) == 1
    assert registry.get("helper1") is v2
    assert registry.query("data.read") == []
    assert [m.id for m in registry.query("mission.validate")] == ["helper1"]


def test_load_directory(tmp_path: Path) -> None:
    registry = ManifestRegistry()
    for agent_id in ("helper1", "mission_engine"):
        payload = _manifest(agent_id, ["data.read"])
        (tmp_path / f"{agent_id}.manifest.json").write_text(json.dumps(payload), encoding="utf-8")

    loaded = registry.load_directory(tmp_path)

    assert loaded == ["helper1", "mission_engine"]
    assert len(registry.all()) == 2


def test_contains_protocol() -> None:
    registry = ManifestRegistry()
    registry.register(AgentManifest.from_dict(_manifest("helper1", ["data.read"])))
    assert "helper1" in registry
    assert "missing" not in registry
