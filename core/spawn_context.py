"""
NEXUSMON - SpawnContext.
Context envelope passed to every spawned agent.
Enforces least-privilege: child capabilities subset of parent capabilities.
Core module: immutable without ADR.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from core.agent_manifest import AgentManifest

MAX_SPAWN_DEPTH = 10


@dataclass(frozen=True)
class SpawnContext:
    session_id: str
    trace_id: str
    depth: int
    capabilities_granted: frozenset[str]
    parent_agent_id: str | None = None
    provenance: tuple[str, ...] = field(default_factory=tuple)

    def spawn_child(
        self,
        child_agent_id: str,
        requested_capabilities: frozenset[str],
        max_depth: int = 3,
    ) -> SpawnContext:
        """
        Create a child context with depth and least-privilege checks.
        """
        effective_max_depth = min(max_depth, MAX_SPAWN_DEPTH)
        if self.depth >= effective_max_depth:
            raise PermissionError(
                f"Spawn depth {self.depth} exceeds max {effective_max_depth} "
                f"(trace_id={self.trace_id})"
            )

        granted = requested_capabilities & self.capabilities_granted
        return SpawnContext(
            session_id=self.session_id,
            trace_id=self.trace_id,
            depth=self.depth + 1,
            capabilities_granted=granted,
            parent_agent_id=child_agent_id,
            provenance=self.provenance + (child_agent_id,),
        )

    @classmethod
    def root(cls, capabilities: frozenset[str], session_id: str | None = None) -> SpawnContext:
        """Create a root context (no parent, depth=0)."""
        return cls(
            session_id=session_id or str(uuid.uuid4()),
            trace_id=str(uuid.uuid4()),
            depth=0,
            capabilities_granted=capabilities,
        )

    @classmethod
    def root_from_manifest(
        cls, manifest: AgentManifest, session_id: str | None = None
    ) -> SpawnContext:
        """Create a root context directly from an AgentManifest."""
        return cls.root(
            capabilities=frozenset(manifest.capabilities),
            session_id=session_id,
        )

    def can_spawn_child_manifest(self, child_manifest: AgentManifest) -> bool:
        """Manifest-oriented spawn depth check."""
        child_max = int(child_manifest.limits.get("max_depth", 0))
        effective_max_depth = min(child_max, MAX_SPAWN_DEPTH)
        return (self.depth + 1) <= effective_max_depth

    def spawn_child_manifest(self, child_manifest: AgentManifest) -> SpawnContext:
        """Spawn child context using manifest limits and declared capabilities."""
        if not self.can_spawn_child_manifest(child_manifest):
            raise PermissionError(
                f"Spawn depth {self.depth + 1} exceeds manifest max "
                f"{int(child_manifest.limits.get('max_depth', 0))} "
                f"(trace_id={self.trace_id})"
            )
        return SpawnContext(
            session_id=self.session_id,
            trace_id=self.trace_id,
            depth=self.depth + 1,
            capabilities_granted=frozenset(child_manifest.capabilities)
            & self.capabilities_granted,
            parent_agent_id=child_manifest.id,
            provenance=self.provenance + (child_manifest.id,),
        )
