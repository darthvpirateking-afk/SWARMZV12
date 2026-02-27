"""NEXUSMON – Agent Runtime Kernel (v1.0)

The living layer between the genome (manifest) and the organism (NEXUSMON).

Every agent loaded by the manifest registry is assigned an AgentRuntime
instance.  The runtime drives the full lifecycle:

    think()    — run the cognition loop
    act()      — produce mission outputs
    validate() — enforce safety policy
    remember() — apply memory policy
    evolve()   — apply XP / trait progression
    emit()     — push events to the cockpit feed

Supporting singletons
---------------------
    EVENT_BUS      SimpleEventBus   — in-process publish/subscribe
    MISSION_ROUTER SimpleMissionRouter — in-process mission dispatch
    MEMORY_STORE   SimpleMemoryStore   — in-process keyed memory

Public surface
--------------
    spawn(agent_id)          -> AgentRuntime   (from registered manifest)
    get_runtime(agent_id)    -> AgentRuntime | None
    list_runtimes()          -> list[dict]     (operator snapshots)
    RUNTIME_REGISTRY         -> RuntimeRegistry singleton
"""

from __future__ import annotations

import logging
import time
import traceback
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# SimpleEventBus — in-process pub/sub, feeds the cockpit event stream
# ---------------------------------------------------------------------------

class SimpleEventBus:
    """Lightweight synchronous event bus with a fixed-depth ring buffer."""

    def __init__(self, maxlen: int = 500):
        self._buffer: List[Dict[str, Any]] = []
        self._maxlen = maxlen
        self._subscribers: List[Callable[[Dict[str, Any]], None]] = []

    def subscribe(self, fn: Callable[[Dict[str, Any]], None]) -> None:
        self._subscribers.append(fn)

    def publish(self, event: Dict[str, Any]) -> None:
        self._buffer.append(event)
        if len(self._buffer) > self._maxlen:
            self._buffer.pop(0)
        for fn in self._subscribers:
            try:
                fn(event)
            except Exception:  # subscriptions must never crash the kernel
                pass

    def recent(self, n: int = 50) -> List[Dict[str, Any]]:
        return self._buffer[-n:]

    def clear(self) -> None:
        self._buffer.clear()


# ---------------------------------------------------------------------------
# SimpleMissionRouter — in-process mission dispatch queue
# ---------------------------------------------------------------------------

class SimpleMissionRouter:
    """Routes outbound missions from agents into the NEXUSMON mission queue."""

    def __init__(self):
        self._queue: List[Dict[str, Any]] = []

    def dispatch(self, agent_id: str, mission: Dict[str, Any]) -> None:
        entry = {
            "agent": agent_id,
            "mission": mission,
            "status": "PENDING",
            "dispatched_at": time.time(),
        }
        self._queue.append(entry)
        logger.debug("[ROUTER] Mission dispatched from %s: %s", agent_id, mission)

    def drain(self) -> List[Dict[str, Any]]:
        """Pop and return all pending missions."""
        pending, self._queue = self._queue[:], []
        return pending

    def pending(self) -> List[Dict[str, Any]]:
        return list(self._queue)


# ---------------------------------------------------------------------------
# SimpleMemoryStore — in-process keyed agent memory
# ---------------------------------------------------------------------------

class SimpleMemoryStore:
    """Per-agent in-memory key-value store supporting all memory policies."""

    def __init__(self):
        self._data: Dict[str, Dict[str, Any]] = {}

    def _ns(self, agent_id: str) -> Dict[str, Any]:
        if agent_id not in self._data:
            self._data[agent_id] = {}
        return self._data[agent_id]

    def get(self, agent_id: str, key: Optional[str] = None) -> Any:
        ns = self._ns(agent_id)
        if key is None:
            return ns
        return ns.get(key)

    def set(self, agent_id: str, key: str, value: Any) -> None:
        self._ns(agent_id)[key] = value

    def append(self, agent_id: str, key: str, value: Any) -> None:
        ns = self._ns(agent_id)
        if key not in ns or not isinstance(ns[key], list):
            ns[key] = []
        ns[key].append(value)

    def clear_agent(self, agent_id: str) -> None:
        self._data.pop(agent_id, None)

    def snapshot(self, agent_id: str) -> Dict[str, Any]:
        return dict(self._ns(agent_id))


# ---------------------------------------------------------------------------
# Module-level singletons (shared across all runtime instances)
# ---------------------------------------------------------------------------

EVENT_BUS = SimpleEventBus()
MISSION_ROUTER = SimpleMissionRouter()
MEMORY_STORE = SimpleMemoryStore()


# ---------------------------------------------------------------------------
# AgentRuntime — the living agent instance
# ---------------------------------------------------------------------------

class AgentRuntime:
    """Execution engine for a single loaded agent manifest.

    Parameters
    ----------
    agent_manifest : AgentManifest
        Genome object returned by ``core.agent_manifest.load_manifest``.
    event_bus : SimpleEventBus
    mission_router : SimpleMissionRouter
    memory_store : SimpleMemoryStore
    cognition_fn : callable | None
        Optional override for the cognition entrypoint.  When *None*, the
        runtime uses a pass-through that returns the input unchanged.
    safety_validators : list[callable] | None
        Optional list of ``(artifact) -> "OK" | "REJECTED"`` callables.
        When *None*, a permissive default is used.
    """

    def __init__(
        self,
        agent_manifest: Any,
        event_bus: SimpleEventBus,
        mission_router: SimpleMissionRouter,
        memory_store: SimpleMemoryStore,
        cognition_fn: Optional[Callable] = None,
        safety_validators: Optional[List[Callable]] = None,
    ):
        m = agent_manifest
        self.manifest = m
        self.id: str = m.id
        self.name: str = m.name
        self.event_bus = event_bus
        self.mission_router = mission_router
        self.memory_store = memory_store

        # Cognition
        self._cognition_fn: Callable = cognition_fn or self._default_cognition

        # Safety
        self._validators: List[Callable] = safety_validators or []

        # Evolution state (persisted in-runtime; can be promoted to DB)
        self.xp: int = 0
        self.traits: List[str] = list(getattr(m, "traits", None) or [])
        self.rank: str = getattr(m, "rank", "E")

        # Diagnostics
        self.last_output: Any = None
        self.last_error: Optional[str] = None
        self.call_count: int = 0
        self.error_count: int = 0
        self.started_at: float = time.time()

        self.emit("runtime_ready", {"agent": self.id, "name": self.name})
        logger.info("[RUNTIME] Agent %s online", self.id)

    # ------------------------------------------------------------------
    # Default no-op cognition (pass-through)
    # ------------------------------------------------------------------

    @staticmethod
    def _default_cognition(input_data: Any) -> Any:
        return input_data

    # ------------------------------------------------------------------
    # emit — push event to the global feed
    # ------------------------------------------------------------------

    def emit(self, event_type: str, data: Any) -> None:
        self.event_bus.publish({
            "agent": self.id,
            "type": event_type,
            "data": data,
            "timestamp": time.time(),
        })

        # Also forward to timeline_store if available (cockpit persistence)
        try:
            from timeline_store import append_event  # type: ignore
            append_event(f"agent.{event_type}", {
                "agent": self.id,
                "data": data,
            })
        except Exception:
            pass

    # ------------------------------------------------------------------
    # validate — run safety policy over an artifact
    # ------------------------------------------------------------------

    def validate(self, artifact: Any) -> bool:
        """Return True when artifact passes all configured validators."""
        for validator in self._validators:
            try:
                result = validator(artifact)
            except Exception as exc:
                self.emit("validator_error", {"error": str(exc)})
                return False
            if result == "REJECTED":
                self.emit("validator_reject", {"artifact": str(artifact)[:256]})
                return False
        # Also enforce manifest safety block_list keywords if present
        try:
            block_list = self.manifest.safety.block_list or []
            if block_list and isinstance(artifact, dict):
                text = str(artifact).lower()
                for term in block_list:
                    if term.lower() in text:
                        self.emit("safety_block", {"term": term})
                        return False
        except Exception:
            pass
        return True

    # ------------------------------------------------------------------
    # remember — apply memory policy
    # ------------------------------------------------------------------

    def remember(self, input_data: Any, output_data: Any) -> None:
        try:
            policy = self.manifest.cognition.memory_policy or "none"
        except AttributeError:
            policy = "none"

        if policy == "none":
            return

        if policy == "short":
            self.memory_store.set(self.id, "last", output_data)

        elif policy == "long":
            self.memory_store.append(self.id, "history", {
                "input": input_data,
                "output": output_data,
                "ts": time.time(),
            })

        elif policy == "episodic":
            ns = self.memory_store.get(self.id)
            if "episode" not in ns:
                self.memory_store.set(self.id, "episode", [])
            self.memory_store.append(self.id, "episode", output_data)

    # ------------------------------------------------------------------
    # evolve — apply XP and unlock traits
    # ------------------------------------------------------------------

    def evolve(self, delta_xp: int = 1) -> None:
        self.xp += delta_xp
        try:
            evo = self.manifest.evolution
            requires = evo.requires or {}
            xp_threshold = requires.get("xp", 0)
            if xp_threshold and self.xp >= xp_threshold:
                for trait in (evo.unlocks or []):
                    if trait not in self.traits:
                        self.traits.append(trait)
                        self.emit("trait_unlocked", {"trait": trait, "xp": self.xp})
        except AttributeError:
            pass

    # ------------------------------------------------------------------
    # think — core cognition loop
    # ------------------------------------------------------------------

    def think(self, input_data: Any) -> Optional[Any]:
        self.call_count += 1
        try:
            output = self._cognition_fn(input_data)
            self.last_output = output

            if not self.validate(output):
                return None

            self.remember(input_data, output)
            self.evolve(1)

            self.emit("cognition", {
                "input": str(input_data)[:512],
                "output": str(output)[:512],
                "call": self.call_count,
            })
            return output

        except Exception as exc:
            self.error_count += 1
            self.last_error = traceback.format_exc()
            self.emit("error", {"error": str(exc), "trace": self.last_error[:1024]})
            return None

    # ------------------------------------------------------------------
    # act — think + mission dispatch
    # ------------------------------------------------------------------

    def act(self, input_data: Any) -> Optional[Any]:
        output = self.think(input_data)
        if output is None:
            return None

        if isinstance(output, dict) and "mission" in output:
            mission = output["mission"]
            self.mission_router.dispatch(self.id, mission)
            self.emit("mission_dispatch", mission)

        return output

    # ------------------------------------------------------------------
    # snapshot — operator-visible state
    # ------------------------------------------------------------------

    def snapshot(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "xp": self.xp,
            "rank": self.rank,
            "traits": self.traits,
            "call_count": self.call_count,
            "error_count": self.error_count,
            "last_error": self.last_error,
            "memory": self.memory_store.snapshot(self.id),
            "uptime_s": round(time.time() - self.started_at, 1),
        }


# ---------------------------------------------------------------------------
# RuntimeRegistry — singleton container for all live AgentRuntime instances
# ---------------------------------------------------------------------------

class RuntimeRegistry:
    """owns all live AgentRuntime instances."""

    def __init__(self):
        self._runtimes: Dict[str, AgentRuntime] = {}

    def register(self, runtime: AgentRuntime) -> None:
        self._runtimes[runtime.id] = runtime

    def get(self, agent_id: str) -> Optional[AgentRuntime]:
        return self._runtimes.get(agent_id)

    def list(self) -> List[AgentRuntime]:
        return list(self._runtimes.values())

    def remove(self, agent_id: str) -> bool:
        if agent_id in self._runtimes:
            del self._runtimes[agent_id]
            return True
        return False

    def clear(self) -> None:
        self._runtimes.clear()

    def snapshots(self) -> List[Dict[str, Any]]:
        return [r.snapshot() for r in self._runtimes.values()]


RUNTIME_REGISTRY = RuntimeRegistry()


# ---------------------------------------------------------------------------
# spawn — convenience factory
# ---------------------------------------------------------------------------

def spawn(
    agent_id: str,
    cognition_fn: Optional[Callable] = None,
    safety_validators: Optional[List[Callable]] = None,
    event_bus: Optional[SimpleEventBus] = None,
    mission_router: Optional[SimpleMissionRouter] = None,
    memory_store: Optional[SimpleMemoryStore] = None,
) -> AgentRuntime:
    """Create an AgentRuntime from a registered manifest and record it.

    Raises
    ------
    KeyError
        If ``agent_id`` is not found in the manifest registry.
    """
    from core.agent_manifest import get_agent  # local import avoids cycles

    manifest = get_agent(agent_id)
    if manifest is None:
        raise KeyError(f"No manifest registered for agent '{agent_id}'")

    runtime = AgentRuntime(
        agent_manifest=manifest,
        event_bus=event_bus or EVENT_BUS,
        mission_router=mission_router or MISSION_ROUTER,
        memory_store=memory_store or MEMORY_STORE,
        cognition_fn=cognition_fn,
        safety_validators=safety_validators,
    )
    RUNTIME_REGISTRY.register(runtime)
    return runtime


def get_runtime(agent_id: str) -> Optional[AgentRuntime]:
    return RUNTIME_REGISTRY.get(agent_id)


def list_runtimes() -> List[Dict[str, Any]]:
    return RUNTIME_REGISTRY.snapshots()
