"""Tests for core/agent_runtime.py — Agent Runtime Kernel."""

import time
import pytest

from core.agent_runtime import (
    AgentRuntime,
    RuntimeRegistry,
    SimpleEventBus,
    SimpleMissionRouter,
    SimpleMemoryStore,
    RUNTIME_REGISTRY,
    EVENT_BUS,
    MISSION_ROUTER,
    MEMORY_STORE,
    spawn,
    get_runtime,
    list_runtimes,
)


# ---------------------------------------------------------------------------
# Minimal stub manifest (mirrors AgentManifest structure, no Pydantic dep)
# ---------------------------------------------------------------------------

class _SafetyStub:
    block_list = []
    validators = []
    max_output_tokens = 2048
    allowed_actions = ["read", "write"]


class _CognitionStub:
    entrypoint = "core.agent_runtime._default"
    processors = []
    memory_policy = "short"


class _MissionsStub:
    accepts = ["test"]
    generates = ["result"]
    autonomy_level = 1


class _EvoStub:
    requires = {"xp": 5}
    unlocks = ["turbo_mode"]


class _EvoBigStub:
    requires = {"xp": 999}
    unlocks = ["never_unlocked"]


class _ManifestStub:
    id = "test-agent"
    name = "Test Agent"
    version = "1.0.0"
    rank = "D"
    traits = []

    def __init__(self, memory_policy="short", evo=None):
        self.cognition = _CognitionStub()
        self.cognition.memory_policy = memory_policy
        self.safety = _SafetyStub()
        self.missions = _MissionsStub()
        self.evolution = evo or _EvoStub()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def bus():
    return SimpleEventBus(maxlen=20)


@pytest.fixture()
def router():
    return SimpleMissionRouter()


@pytest.fixture()
def store():
    return SimpleMemoryStore()


@pytest.fixture()
def stub_manifest():
    return _ManifestStub()


@pytest.fixture()
def runtime(stub_manifest, bus, router, store):
    return AgentRuntime(stub_manifest, bus, router, store)


# ---------------------------------------------------------------------------
# SimpleEventBus
# ---------------------------------------------------------------------------

class TestSimpleEventBus:
    def test_publish_and_recent(self, bus):
        bus.publish({"type": "test", "data": 1})
        bus.publish({"type": "test", "data": 2})
        events = bus.recent(10)
        assert len(events) == 2
        assert events[-1]["data"] == 2

    def test_maxlen_ring(self):
        bus = SimpleEventBus(maxlen=3)
        for i in range(5):
            bus.publish({"i": i})
        assert len(bus.recent(10)) == 3
        assert bus.recent(10)[-1]["i"] == 4

    def test_subscribe_callback(self, bus):
        received = []
        bus.subscribe(received.append)
        bus.publish({"msg": "hello"})
        assert len(received) == 1
        assert received[0]["msg"] == "hello"

    def test_subscriber_exception_does_not_crash(self, bus):
        def bad_sub(_):
            raise RuntimeError("boom")
        bus.subscribe(bad_sub)
        bus.publish({"safe": True})  # must not raise
        assert len(bus.recent(5)) == 1

    def test_clear(self, bus):
        bus.publish({"x": 1})
        bus.clear()
        assert bus.recent(10) == []


# ---------------------------------------------------------------------------
# SimpleMissionRouter
# ---------------------------------------------------------------------------

class TestSimpleMissionRouter:
    def test_dispatch_and_pending(self, router):
        router.dispatch("agent-1", {"type": "scan"})
        pending = router.pending()
        assert len(pending) == 1
        assert pending[0]["agent"] == "agent-1"
        assert pending[0]["status"] == "PENDING"

    def test_drain_clears_queue(self, router):
        router.dispatch("agent-1", {"type": "scan"})
        router.dispatch("agent-2", {"type": "destroy"})
        drained = router.drain()
        assert len(drained) == 2
        assert router.pending() == []


# ---------------------------------------------------------------------------
# SimpleMemoryStore
# ---------------------------------------------------------------------------

class TestSimpleMemoryStore:
    def test_set_and_get(self, store):
        store.set("a1", "key", "value")
        assert store.get("a1", "key") == "value"

    def test_get_namespace(self, store):
        store.set("a1", "x", 1)
        ns = store.get("a1")
        assert "x" in ns

    def test_append(self, store):
        store.append("a1", "log", "first")
        store.append("a1", "log", "second")
        assert store.get("a1", "log") == ["first", "second"]

    def test_clear_agent(self, store):
        store.set("a1", "x", 99)
        store.clear_agent("a1")
        assert store.get("a1", "x") is None

    def test_snapshot(self, store):
        store.set("a1", "k", "v")
        snap = store.snapshot("a1")
        assert snap["k"] == "v"
        # mutation of snapshot does not affect store
        snap["k"] = "mutated"
        assert store.get("a1", "k") == "v"


# ---------------------------------------------------------------------------
# AgentRuntime — construction
# ---------------------------------------------------------------------------

class TestAgentRuntimeConstruction:
    def test_runtime_initialises(self, runtime):
        assert runtime.id == "test-agent"
        assert runtime.name == "Test Agent"
        assert runtime.xp == 0
        assert runtime.call_count == 0

    def test_runtime_emits_ready_event(self, bus, stub_manifest, router, store):
        AgentRuntime(stub_manifest, bus, router, store)
        events = bus.recent(10)
        types = [e["type"] for e in events]
        assert "runtime_ready" in types

    def test_uptime_positive(self, runtime):
        snap = runtime.snapshot()
        assert snap["uptime_s"] >= 0


# ---------------------------------------------------------------------------
# AgentRuntime — emit
# ---------------------------------------------------------------------------

class TestAgentRuntimeEmit:
    def test_emit_puts_event_in_bus(self, runtime, bus):
        runtime.emit("custom_event", {"val": 42})
        events = bus.recent(10)
        custom = [e for e in events if e["type"] == "custom_event"]
        assert len(custom) == 1
        assert custom[0]["data"]["val"] == 42

    def test_emit_includes_agent_id(self, runtime, bus):
        runtime.emit("ping", {})
        pings = [e for e in bus.recent(10) if e["type"] == "ping"]
        assert pings[0]["agent"] == "test-agent"


# ---------------------------------------------------------------------------
# AgentRuntime — validate
# ---------------------------------------------------------------------------

class TestAgentRuntimeValidate:
    def test_validate_passes_with_no_validators(self, runtime):
        assert runtime.validate({"result": "ok"}) is True

    def test_validate_fails_on_rejection(self, stub_manifest, bus, router, store):
        def reject_all(artifact):
            return "REJECTED"
        rt = AgentRuntime(stub_manifest, bus, router, store, safety_validators=[reject_all])
        assert rt.validate("anything") is False

    def test_validate_emits_reject_event(self, stub_manifest, bus, router, store):
        def reject_all(artifact):
            return "REJECTED"
        rt = AgentRuntime(stub_manifest, bus, router, store, safety_validators=[reject_all])
        rt.validate("payload")
        rejects = [e for e in bus.recent(20) if e["type"] == "validator_reject"]
        assert len(rejects) == 1

    def test_validate_block_list_term(self, bus, router, store):
        manifest = _ManifestStub()
        manifest.safety.block_list = ["danger"]
        rt = AgentRuntime(manifest, bus, router, store)
        assert rt.validate({"content": "this is danger"}) is False

    def test_validate_block_list_allows_clean(self, bus, router, store):
        manifest = _ManifestStub()
        manifest.safety.block_list = ["danger"]
        rt = AgentRuntime(manifest, bus, router, store)
        assert rt.validate({"content": "all good"}) is True

    def test_validator_exception_returns_false(self, stub_manifest, bus, router, store):
        def exploding_validator(artifact):
            raise ValueError("internal error")
        rt = AgentRuntime(stub_manifest, bus, router, store, safety_validators=[exploding_validator])
        assert rt.validate("payload") is False


# ---------------------------------------------------------------------------
# AgentRuntime — remember
# ---------------------------------------------------------------------------

class TestAgentRuntimeRemember:
    def test_remember_none_policy_no_write(self, bus, router, store):
        manifest = _ManifestStub(memory_policy="none")
        rt = AgentRuntime(manifest, bus, router, store)
        rt.remember("in", "out")
        assert store.snapshot("test-agent") == {}

    def test_remember_short_policy(self, runtime, store):
        runtime.manifest.cognition.memory_policy = "short"
        runtime.remember("input", "output")
        assert store.get("test-agent", "last") == "output"

    def test_remember_long_policy(self, bus, router, store):
        manifest = _ManifestStub(memory_policy="long")
        rt = AgentRuntime(manifest, bus, router, store)
        rt.remember("i1", "o1")
        rt.remember("i2", "o2")
        history = store.get("test-agent", "history")
        assert len(history) == 2
        assert history[0]["input"] == "i1"

    def test_remember_episodic_policy(self, bus, router, store):
        manifest = _ManifestStub(memory_policy="episodic")
        rt = AgentRuntime(manifest, bus, router, store)
        rt.remember("i", "ep1")
        rt.remember("i", "ep2")
        episode = store.get("test-agent", "episode")
        assert episode == ["ep1", "ep2"]


# ---------------------------------------------------------------------------
# AgentRuntime — evolve
# ---------------------------------------------------------------------------

class TestAgentRuntimeEvolve:
    def test_evolve_accumulates_xp(self, runtime):
        runtime.evolve(3)
        assert runtime.xp == 3

    def test_evolve_unlocks_trait_at_threshold(self, runtime, bus):
        # threshold is 5 XP in _EvoStub
        runtime.evolve(5)
        assert "turbo_mode" in runtime.traits
        unlocked_events = [e for e in bus.recent(20) if e["type"] == "trait_unlocked"]
        assert len(unlocked_events) == 1

    def test_evolve_no_double_unlock(self, runtime):
        runtime.evolve(5)
        runtime.evolve(5)
        assert runtime.traits.count("turbo_mode") == 1

    def test_evolve_below_threshold_no_unlock(self, runtime):
        runtime.evolve(2)
        assert "turbo_mode" not in runtime.traits

    def test_evolve_high_threshold_not_unlocked(self, bus, router, store):
        manifest = _ManifestStub(evo=_EvoBigStub())
        rt = AgentRuntime(manifest, bus, router, store)
        rt.evolve(10)
        assert "never_unlocked" not in rt.traits


# ---------------------------------------------------------------------------
# AgentRuntime — think
# ---------------------------------------------------------------------------

class TestAgentRuntimeThink:
    def test_think_returns_output(self, runtime):
        out = runtime.think({"query": "hello"})
        assert out == {"query": "hello"}  # default cognition is pass-through

    def test_think_increments_call_count(self, runtime):
        runtime.think("a")
        runtime.think("b")
        assert runtime.call_count == 2

    def test_think_emits_cognition_event(self, runtime, bus):
        runtime.think("x")
        cog_events = [e for e in bus.recent(20) if e["type"] == "cognition"]
        assert len(cog_events) == 1

    def test_think_with_custom_cognition(self, stub_manifest, bus, router, store):
        def double(x):
            return x * 2
        rt = AgentRuntime(stub_manifest, bus, router, store, cognition_fn=double)
        assert rt.think(4) == 8

    def test_think_returns_none_on_rejection(self, stub_manifest, bus, router, store):
        rt = AgentRuntime(stub_manifest, bus, router, store, safety_validators=[lambda _: "REJECTED"])
        assert rt.think("data") is None

    def test_think_handles_exception(self, stub_manifest, bus, router, store):
        def boom(_):
            raise RuntimeError("crashed")
        rt = AgentRuntime(stub_manifest, bus, router, store, cognition_fn=boom)
        result = rt.think("trigger")
        assert result is None
        assert rt.last_error is not None
        assert rt.error_count == 1

    def test_think_emits_error_event_on_crash(self, stub_manifest, bus, router, store):
        def boom(_):
            raise ValueError("bad")
        rt = AgentRuntime(stub_manifest, bus, router, store, cognition_fn=boom)
        rt.think("x")
        errors = [e for e in bus.recent(20) if e["type"] == "error"]
        assert len(errors) == 1


# ---------------------------------------------------------------------------
# AgentRuntime — act
# ---------------------------------------------------------------------------

class TestAgentRuntimeAct:
    def test_act_dispatches_mission(self, router, bus, store):
        manifest = _ManifestStub()
        def cognition_with_mission(data):
            return {"mission": {"type": "scan", "target": "sector-7"}}
        rt = AgentRuntime(manifest, bus, router, store, cognition_fn=cognition_with_mission)
        rt.act("go")
        pending = router.pending()
        assert len(pending) == 1
        assert pending[0]["mission"]["type"] == "scan"

    def test_act_emits_mission_dispatch_event(self, bus, router, store):
        manifest = _ManifestStub()
        def emit_mission(_):
            return {"mission": {"type": "recon"}}
        rt = AgentRuntime(manifest, bus, router, store, cognition_fn=emit_mission)
        rt.act("trigger")
        dispatches = [e for e in bus.recent(20) if e["type"] == "mission_dispatch"]
        assert len(dispatches) == 1

    def test_act_no_mission_when_output_none(self, stub_manifest, bus, router, store):
        rt = AgentRuntime(stub_manifest, bus, router, store, safety_validators=[lambda _: "REJECTED"])
        rt.act("data")
        assert router.pending() == []

    def test_act_no_mission_when_output_plain_dict(self, runtime, router):
        runtime.act({"result": "data"})
        assert router.pending() == []


# ---------------------------------------------------------------------------
# AgentRuntime — snapshot
# ---------------------------------------------------------------------------

class TestAgentRuntimeSnapshot:
    def test_snapshot_keys(self, runtime):
        snap = runtime.snapshot()
        for key in ("id", "name", "xp", "rank", "traits", "call_count", "error_count", "uptime_s", "memory"):
            assert key in snap

    def test_snapshot_reflects_state(self, runtime):
        runtime.think("hello")
        snap = runtime.snapshot()
        assert snap["call_count"] == 1
        assert snap["xp"] == 1  # evolve(1) called in think


# ---------------------------------------------------------------------------
# RuntimeRegistry
# ---------------------------------------------------------------------------

class TestRuntimeRegistry:
    def test_register_and_get(self, stub_manifest, bus, router, store):
        reg = RuntimeRegistry()
        rt = AgentRuntime(stub_manifest, bus, router, store)
        reg.register(rt)
        assert reg.get("test-agent") is rt

    def test_list_returns_all(self, stub_manifest, bus, router, store):
        reg = RuntimeRegistry()
        rt = AgentRuntime(stub_manifest, bus, router, store)
        reg.register(rt)
        assert rt in reg.list()

    def test_remove(self, stub_manifest, bus, router, store):
        reg = RuntimeRegistry()
        rt = AgentRuntime(stub_manifest, bus, router, store)
        reg.register(rt)
        assert reg.remove("test-agent") is True
        assert reg.get("test-agent") is None

    def test_remove_missing_returns_false(self):
        reg = RuntimeRegistry()
        assert reg.remove("ghost") is False

    def test_snapshots(self, stub_manifest, bus, router, store):
        reg = RuntimeRegistry()
        rt = AgentRuntime(stub_manifest, bus, router, store)
        reg.register(rt)
        snaps = reg.snapshots()
        assert len(snaps) == 1
        assert snaps[0]["id"] == "test-agent"

    def test_clear(self, stub_manifest, bus, router, store):
        reg = RuntimeRegistry()
        rt = AgentRuntime(stub_manifest, bus, router, store)
        reg.register(rt)
        reg.clear()
        assert reg.list() == []


# ---------------------------------------------------------------------------
# spawn / get_runtime / list_runtimes  (integration with manifest registry)
# ---------------------------------------------------------------------------

class TestSpawnIntegration:
    def test_spawn_raises_without_manifest(self):
        with pytest.raises(KeyError, match="no-such-agent"):
            spawn("no-such-agent")

    def test_spawn_with_registered_manifest(self):
        """Register a stub in the manifest registry then spawn a runtime."""
        from core.agent_manifest import REGISTRY as MANIFEST_REGISTRY

        # Build a minimal Pydantic-compatible manifest via register_manifest
        from core.agent_manifest import register_manifest

        data = {
            "id": "spawn-test-agent",
            "name": "Spawn Test",
            "version": "1.0.0",
            "persona": {
                "summary": "test persona",
                "directives": ["do good"],
                "constraints": ["no harm"],
            },
            "cognition": {
                "entrypoint": "core.agent_runtime",
                "processors": [],
                "memory_policy": "short",
            },
            "missions": {
                "accepts": ["test"],
                "generates": [],
                "autonomy_level": 0,
            },
            "safety": {
                "validators": [],
                "max_scope": "read",
            },
            "evolution": {
                "requires": {"xp": 100},
                "unlocks": [],
            },
        }
        register_manifest(data)

        rt = spawn("spawn-test-agent")
        assert rt.id == "spawn-test-agent"
        assert get_runtime("spawn-test-agent") is rt

        # Cleanup
        MANIFEST_REGISTRY.remove("spawn-test-agent")
        RUNTIME_REGISTRY.remove("spawn-test-agent")

    def test_list_runtimes_returns_snapshots(self, stub_manifest, bus, router, store):
        RUNTIME_REGISTRY.clear()
        rt = AgentRuntime(stub_manifest, bus, router, store)
        RUNTIME_REGISTRY.register(rt)
        snaps = list_runtimes()
        assert any(s["id"] == "test-agent" for s in snaps)
        RUNTIME_REGISTRY.clear()
