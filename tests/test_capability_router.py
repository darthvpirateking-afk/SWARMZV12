"""CapabilityRouter unit tests."""
from __future__ import annotations

from core.agent_manifest import AgentManifest
from core.capability_router import CapabilityRouter, RouterWeights
from core.manifest_registry import ManifestRegistry


def _manifest(
    agent_id: str,
    capabilities: list[str],
    *,
    trust: float,
    memory_mb: int,
    cpu_pct: float,
    spawn_policy: str = "ephemeral",
    fallback_agent_id: str | None = None,
) -> AgentManifest:
    error_modes: dict[str, object] = {
        "on_validation_failure": "reject",
        "on_dependency_missing": "defer",
        "on_runtime_exception": "fallback",
        "max_retries": 0,
    }
    if fallback_agent_id is not None:
        error_modes["fallback_agent_id"] = fallback_agent_id

    return AgentManifest.from_dict(
        {
            "id": agent_id,
            "version": "0.1.0",
            "capabilities": capabilities,
            "inputs": {"query": {"type": "string", "required": True}},
            "outputs": {"result": {"type": "object", "required": True}},
            "spawn_policy": spawn_policy,
            "constraints": {
                "max_memory_mb": memory_mb,
                "max_cpu_percent": cpu_pct,
                "max_spawn_depth": 3,
                "network_access": False,
                "filesystem_access": "none",
                "allowed_capabilities": capabilities,
                "trust_level": trust,
            },
            "error_modes": error_modes,
        }
    )


def _router() -> CapabilityRouter:
    registry = ManifestRegistry()
    registry.register(
        _manifest(
            "helper1",
            ["data.read", "agent.introspect"],
            trust=0.90,
            memory_mb=256,
            cpu_pct=20,
            fallback_agent_id="reality_gate",
        )
    )
    registry.register(
        _manifest(
            "mission_engine",
            ["mission.execute", "mission.validate", "agent.spawn"],
            trust=0.85,
            memory_mb=512,
            cpu_pct=40,
            spawn_policy="singleton",
        )
    )
    registry.register(
        _manifest(
            "reality_gate",
            ["gate.evaluate", "data.read"],
            trust=0.95,
            memory_mb=128,
            cpu_pct=15,
            spawn_policy="pooled",
            fallback_agent_id="helper1",
        )
    )
    return CapabilityRouter(registry=registry)


def test_weights_must_sum_to_one() -> None:
    try:
        RouterWeights(match=0.5, trust=0.5, cost=0.2)
    except ValueError as exc:
        assert "sum to 1.0" in str(exc)
    else:
        raise AssertionError("Expected RouterWeights validation error")


def test_routes_are_ranked_and_non_empty() -> None:
    router = _router()
    results = router.route(["data.read"])
    assert results
    assert results[0].agent_id in {"helper1", "reality_gate"}
    assert all(candidate.match_score > 0 for candidate in results)


def test_route_is_deterministic_over_100_runs() -> None:
    router = _router()
    expected = [c.agent_id for c in router.route(["data.read", "gate.evaluate"])]
    for _ in range(100):
        actual = [c.agent_id for c in router.route(["data.read", "gate.evaluate"])]
        assert actual == expected


def test_capability_grant_gate_blocks_escalation() -> None:
    router = _router()
    results = router.route(
        ["mission.execute"],
        granted_capabilities=frozenset({"data.read", "agent.introspect"}),
    )
    assert results == []


def test_resolve_fallback_returns_declared_fallback() -> None:
    router = _router()
    fallback = router.resolve_fallback("helper1")
    assert fallback is not None
    assert fallback.id == "reality_gate"


def test_resolve_fallback_respects_depth_cap() -> None:
    router = _router()
    assert router.resolve_fallback("helper1", depth=3) is None


def test_detect_conflicts_for_singletons() -> None:
    registry = ManifestRegistry()
    registry.register(
        _manifest(
            "engine_a",
            ["mission.execute"],
            trust=0.9,
            memory_mb=128,
            cpu_pct=10,
            spawn_policy="singleton",
        )
    )
    registry.register(
        _manifest(
            "engine_b",
            ["mission.execute"],
            trust=0.8,
            memory_mb=256,
            cpu_pct=20,
            spawn_policy="singleton",
        )
    )
    conflicts = CapabilityRouter(registry).detect_conflicts(["engine_a", "engine_b"])
    assert conflicts
    assert "mission.execute" in conflicts[0]
