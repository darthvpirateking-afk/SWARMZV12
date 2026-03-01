"""
NEXUSMON - CapabilityRouter.
Scores, ranks, and gates agent selection for a given task.
All routing decisions are deterministic and manifest-driven.
Core module: weights configurable; algorithm changes require ADR.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any

from core.agent_manifest import AgentManifest
from core.manifest_registry import ManifestRegistry

MAX_FALLBACK_DEPTH = 3


@dataclass(frozen=True)
class RouteCandidate:
    agent_id: str
    match_score: float
    trust_level: float
    cost_estimate: float
    composite: float
    reason: str


@dataclass
class RouterWeights:
    """Operator-configurable scoring weights. Must sum to 1.0."""

    match: float = 0.60
    trust: float = 0.30
    cost: float = 0.10

    def __post_init__(self) -> None:
        total = self.match + self.trust + self.cost
        if not math.isclose(total, 1.0, rel_tol=1e-6):
            raise ValueError(f"RouterWeights must sum to 1.0, got {total}")


class CapabilityRouter:
    def __init__(self, registry: ManifestRegistry, weights: RouterWeights | None = None) -> None:
        self._registry = registry
        self._weights = weights or RouterWeights()

    def route(
        self,
        task_capabilities: list[str],
        granted_capabilities: frozenset[str] | None = None,
    ) -> list[RouteCandidate]:
        """Route a task to ranked agent candidates."""
        task_set = frozenset(task_capabilities)
        candidates: list[RouteCandidate] = []

        for manifest in self._registry.all():
            manifest_caps = self._caps(manifest)
            if granted_capabilities is not None and not manifest_caps.issubset(
                granted_capabilities
            ):
                continue

            score = self._score(manifest, task_set)
            if score.match_score > 0:
                candidates.append(score)

        return sorted(
            candidates,
            key=lambda c: (
                -c.composite,
                -c.match_score,
                -c.trust_level,
                c.cost_estimate,
                c.agent_id,
            ),
        )

    def resolve_fallback(
        self,
        agent_id: str,
        visited: set[str] | None = None,
        depth: int = 0,
    ) -> AgentManifest | None:
        """
        Walk the fallback chain declared in error_modes.fallback_agent_id.
        Returns the first declared fallback agent, or None if chain is exhausted.
        """
        if depth >= MAX_FALLBACK_DEPTH:
            return None
        if visited is None:
            visited = set()

        manifest = self._registry.get(agent_id)
        if manifest is None or agent_id in visited:
            return None

        fallback_id = self._fallback_agent_id(manifest)
        if fallback_id is None:
            return None

        visited.add(agent_id)
        fallback = self._registry.get(fallback_id)
        if fallback is not None:
            return fallback

        return self.resolve_fallback(fallback_id, visited, depth + 1)

    def detect_conflicts(self, agent_ids: list[str]) -> list[str]:
        """
        Detect capability conflicts between singleton agents in a proposed chain.
        Returns human-readable conflict descriptions.
        """
        conflicts: list[str] = []
        singleton_caps: dict[str, str] = {}

        for agent_id in agent_ids:
            manifest = self._registry.get(agent_id)
            if manifest is None:
                continue
            if self._spawn_policy_value(manifest) == "singleton":
                for cap in self._caps(manifest):
                    if cap in singleton_caps:
                        conflicts.append(
                            f"Capability '{cap}' claimed by singleton agents "
                            f"'{singleton_caps[cap]}' and '{agent_id}'"
                        )
                    else:
                        singleton_caps[cap] = agent_id

        return conflicts

    def allowed_capabilities(
        self, manifest: AgentManifest, granted_subset: list[str] | None = None
    ) -> list[str]:
        """Return deterministic allowed capability set with escalation protection."""
        declared = set(manifest.capabilities)
        if granted_subset is None:
            return sorted(declared)
        granted = set(granted_subset)
        if not granted.issubset(declared):
            raise ValueError(
                "Granted capabilities exceed declared manifest capabilities"
            )
        return sorted(granted)

    def _score(self, manifest: AgentManifest, task_set: frozenset[str]) -> RouteCandidate:
        matched = task_set & self._caps(manifest)
        match_score = len(matched) / len(task_set) if task_set else 0.0
        trust_level = self._constraint_float(manifest, "trust_level", 0.5)

        mem_cost = (self._constraint_float(manifest, "max_memory_mb", 256.0) or 256.0) / 4096
        cpu_cost = (self._constraint_float(manifest, "max_cpu_percent", 25.0) or 25.0) / 100
        cost_estimate = min((mem_cost + cpu_cost) / 2, 1.0)

        weights = self._weights
        composite = (
            (match_score * weights.match)
            + (trust_level * weights.trust)
            - (cost_estimate * weights.cost)
        )

        reason = (
            f"matched {len(matched)}/{len(task_set)} capabilities"
            f"; trust={trust_level:.2f}"
            f"; cost={cost_estimate:.2f}"
        )

        return RouteCandidate(
            agent_id=manifest.id,
            match_score=match_score,
            trust_level=trust_level,
            cost_estimate=cost_estimate,
            composite=composite,
            reason=reason,
        )

    @staticmethod
    def _caps(manifest: Any) -> set[str]:
        raw = getattr(manifest, "capabilities", [])
        return {str(c) for c in raw}

    @staticmethod
    def _spawn_policy_value(manifest: Any) -> str:
        raw = getattr(manifest, "spawn_policy", "")
        if isinstance(raw, str):
            return raw
        return str(getattr(raw, "value", ""))

    @staticmethod
    def _fallback_agent_id(manifest: Any) -> str | None:
        error_modes = getattr(manifest, "error_modes", None)
        if error_modes is None:
            return None
        val = getattr(error_modes, "fallback_agent_id", None)
        return str(val) if val else None

    @staticmethod
    def _constraint_float(manifest: Any, key: str, default: float) -> float:
        constraints = getattr(manifest, "constraints", None)
        if constraints is None:
            constraints = SimpleNamespace()
        raw = getattr(constraints, key, default)
        try:
            return float(raw)
        except Exception:
            return default
