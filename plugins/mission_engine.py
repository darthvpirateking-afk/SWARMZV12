from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.agent_manifest import AgentManifest
from core.observability import AgentEvent, ObservabilityEmitter
from core.spawn_context import SpawnContext

emitter = ObservabilityEmitter(success_sample_rate=1.0)


@dataclass
class MissionEngineConfig:
    version: str = "0.1.0"


class MissionEnginePlugin:
    """Canonical kernel-lane mission engine plugin (additive, deterministic)."""

    def __init__(self) -> None:
        self.config: MissionEngineConfig | None = None
        self.manifest: AgentManifest | None = None
        self._active = False
        self._trace_id = ""

    async def on_init(self, manifest: AgentManifest, context: SpawnContext) -> None:
        self.manifest = manifest
        self.config = MissionEngineConfig()
        self._trace_id = context.trace_id
        emitter.emit(
            AgentEvent(
                agent_id=manifest.id,
                trace_id=self._trace_id,
                session_id=context.session_id,
                event="plugin.mission_engine.init",
                decision="initialized",
                inputs_hash="",
                outcome="success",
                payload={"version": self.config.version},
            )
        )

    async def on_activate(self, context: SpawnContext) -> None:
        if self._active:
            return
        self._active = True
        emitter.emit(
            AgentEvent(
                agent_id=self.manifest.id if self.manifest else "mission_engine@0.1.0",
                trace_id=self._trace_id,
                session_id=context.session_id,
                event="plugin.mission_engine.activate",
                decision="activated",
                inputs_hash="",
                outcome="success",
                payload={"sandbox": "process", "ephemeral": True},
            )
        )

    async def run(self, template: dict[str, Any], payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if not self._active:
            raise RuntimeError("mission_engine not activated")

        template_id = str(template.get("id", ""))
        steps = list(template.get("steps", []))
        if not template_id or not isinstance(steps, list):
            result = {"error": "invalid_template"}
            outcome = "failure"
        else:
            result = {
                "template_id": template_id,
                "step_count": len(steps),
                "received_payload": payload or {},
                "status": "executed",
            }
            outcome = "success"

        emitter.emit(
            AgentEvent(
                agent_id=self.manifest.id if self.manifest else "mission_engine@0.1.0",
                trace_id=self._trace_id,
                event="plugin.mission_engine.run",
                decision=template_id or "invalid",
                inputs_hash="",
                outcome=outcome,
                payload={"step_count": len(steps) if isinstance(steps, list) else 0},
            )
        )
        return result

    async def on_deactivate(self, context: SpawnContext) -> None:
        if not self._active:
            return
        self._active = False
        emitter.emit(
            AgentEvent(
                agent_id=self.manifest.id if self.manifest else "mission_engine@0.1.0",
                trace_id=self._trace_id,
                session_id=context.session_id,
                event="plugin.mission_engine.deactivate",
                decision="deactivated",
                inputs_hash="",
                outcome="success",
            )
        )

    def unload(self) -> None:
        return None
