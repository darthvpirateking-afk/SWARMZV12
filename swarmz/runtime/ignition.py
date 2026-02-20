from typing import Callable, Dict, List, Optional
from dataclasses import dataclass, field
import logging
import time

logger = logging.getLogger("swarmz.ignition")
logger.setLevel(logging.INFO)

@dataclass
class IgnitionEvent:
    """A single lifecycle event fired during system startup."""
    name: str
    timestamp: float
    metadata: dict = field(default_factory=dict)

@dataclass
class RuntimeIgnitionState:
    """Tracks ignition progress for auditability and operator visibility."""
    started: bool = False
    completed: bool = False
    events: List[IgnitionEvent] = field(default_factory=list)

    def record(self, name: str, metadata: Optional[dict] = None):
        evt = IgnitionEvent(
            name=name,
            timestamp=time.time(),
            metadata=metadata or {}
        )
        self.events.append(evt)
        logger.info(f"[IGNITION] {name} :: {evt.metadata}")

class RuntimeIgnition:
    """
    The ignition layer for SWARMZ.
    Responsible for deterministic startup sequencing and lifecycle events.
    """

    def __init__(self):
        self.state = RuntimeIgnitionState()
        self._steps: List[Callable[[RuntimeIgnitionState], None]] = []

    def register_step(self, fn: Callable[[RuntimeIgnitionState], None]):
        """Register a deterministic startup step."""
        self._steps.append(fn)

    def ignite(self):
        """Execute all registered startup steps in strict order."""
        if self.state.started:
            raise RuntimeError("Ignition already triggered")

        self.state.record("ignition_start")
        self.state.started = True

        for step in self._steps:
            step(self.state)

        self.state.record("ignition_complete")
        self.state.completed = True

        return self.state

# ---------------------------------------------------------------------------
# DEFAULT SYSTEM STEPS
# These are minimal, operator-grade startup steps.
# The agent can expand this list as SWARMZ grows.
# ---------------------------------------------------------------------------

def step_load_kernels(state: RuntimeIgnitionState):
    state.record("load_kernels", {"status": "ok"})

def step_load_patchpacks(state: RuntimeIgnitionState):
    state.record("load_patchpacks", {"status": "ok"})

def step_load_missions(state: RuntimeIgnitionState):
    state.record("load_missions", {"status": "ok"})

def build_default_ignition() -> RuntimeIgnition:
    """Factory for a fully wired ignition sequence."""
    ign = RuntimeIgnition()
    ign.register_step(step_load_kernels)
    ign.register_step(step_load_patchpacks)
    ign.register_step(step_load_missions)
    return ign