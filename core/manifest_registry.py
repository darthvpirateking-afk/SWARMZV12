"""
NEXUSMON - ManifestRegistry.
In-memory registry indexed by agent ID and capability token.
Core module: API shape frozen at v0.1. Immutable without ADR.
"""
from __future__ import annotations

from pathlib import Path

from core.agent_manifest import AgentManifest


class ManifestRegistry:
    """
    Loads, validates, and indexes agent manifests.
    Query by agent ID or capability token.
    """

    def __init__(self) -> None:
        self._by_id: dict[str, AgentManifest] = {}
        self._by_capability: dict[str, list[AgentManifest]] = {}

    def register(self, manifest: AgentManifest) -> None:
        """Register a manifest. Duplicate IDs are rejected (append-only semantics)."""
        if manifest.id in self._by_id:
            raise ValueError(f"Manifest with id={manifest.id} already registered")

        self._by_id[manifest.id] = manifest
        for cap in manifest.capabilities:
            bucket = self._by_capability.setdefault(cap, [])
            bucket.append(manifest)

    def load_directory(self, path: Path) -> list[str]:
        """
        Load all *.manifest.json files from a directory.
        Returns list of loaded agent IDs.
        Raises ValueError on any schema violation.
        """
        loaded: list[str] = []
        for manifest_path in sorted(path.glob("*.manifest.json")):
            manifest = AgentManifest.from_file(manifest_path)
            self.register(manifest)
            loaded.append(manifest.id)
        return loaded

    def get(self, agent_id: str) -> AgentManifest | None:
        """Retrieve a manifest by agent ID."""
        return self._by_id.get(agent_id)

    def query(self, capability: str) -> list[AgentManifest]:
        """Return all agents that declare a given capability token."""
        return list(self._by_capability.get(capability, []))

    def all(self) -> list[AgentManifest]:
        """Return all registered manifests."""
        return list(self._by_id.values())

    def capabilities(self) -> set[str]:
        """Return all known capability tokens across all agents."""
        return set(self._by_capability.keys())

    def clear(self) -> None:
        self._by_id.clear()
        self._by_capability.clear()

    def list_ids(self) -> list[str]:
        """Return registered manifest IDs."""
        return list(self._by_id.keys())

    def __len__(self) -> int:
        return len(self._by_id)

    def __contains__(self, agent_id: str) -> bool:
        return agent_id in self._by_id


REGISTRY = ManifestRegistry()
