"""Bridge-compatible manifest API with v1 schema enforcement for seed manifests."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

from core.registry import registry as v1_registry


@dataclass(frozen=True)
class AgentManifest:
    """Frozen v0.1 kernel manifest model (compatibly derived from current schema)."""

    id: str
    version: str
    capabilities: list[str]
    limits: dict[str, int]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AgentManifest:
        limits_raw = data.get("limits")
        if not isinstance(limits_raw, dict):
            constraints = data.get("constraints", {}) if isinstance(data, dict) else {}
            limits_raw = {
                "max_depth": constraints.get("max_spawn_depth", 0),
                "max_children": constraints.get("max_children", 0),
            }

        return cls(
            id=str(data["id"]),
            version=str(data["version"]),
            capabilities=list(data.get("capabilities", [])),
            limits={
                "max_depth": int(limits_raw.get("max_depth", 0)),
                "max_children": int(limits_raw.get("max_children", 0)),
            },
        )

    @classmethod
    def from_file(cls, path: str | Path) -> AgentManifest:
        payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
        errors = validate_dict(payload)
        if errors:
            raise ValueError("\n".join(errors))
        return cls.from_dict(payload)


@dataclass
class _ManifestEnvelope:
    payload: dict[str, Any]
    id: str
    version: str
    name: str
    rank: str
    traits: list[str]
    capabilities: list[str]
    spawn_policy: Any
    cognition: Any
    safety: Any
    missions: Any
    evolution: Any

    def model_dump(self) -> dict[str, Any]:
        return dict(self.payload)


class _CompatibilityRegistry:
    def __init__(self) -> None:
        self._store: dict[str, _ManifestEnvelope] = {}

    def register(self, manifest: _ManifestEnvelope) -> _ManifestEnvelope:
        self._store[manifest.id] = manifest
        return manifest

    def get(self, agent_id: str) -> _ManifestEnvelope | None:
        if agent_id in self._store:
            return self._store[agent_id]

        if "@" not in agent_id:
            candidates = [key for key in self._store if key.startswith(f"{agent_id}@")]
            if candidates:
                return self._store[sorted(candidates)[-1]]
            for manifest in self._store.values():
                alias = str(manifest.payload.get("extensions", {}).get("legacy_alias", "")).strip()
                if alias == agent_id:
                    return manifest

        return None

    def list(self) -> list[_ManifestEnvelope]:
        return [self._store[key] for key in sorted(self._store)]

    def remove(self, agent_id: str) -> bool:
        if agent_id in self._store:
            del self._store[agent_id]
            return True
        return False

    def clear(self) -> None:
        self._store.clear()

    def __len__(self) -> int:
        return len(self._store)


REGISTRY = _CompatibilityRegistry()


def _as_runtime_defaults(data: dict[str, Any]) -> tuple[Any, Any, Any, Any]:
    cognition = SimpleNamespace(entrypoint="", processors=[], memory_policy="short")
    safety = SimpleNamespace(block_list=[], validators=[], max_scope="read")
    missions = SimpleNamespace(accepts=[], generates=[], autonomy_level=0)
    evolution = SimpleNamespace(requires={"xp": 0}, unlocks=[])

    if "cognition" in data:
        raw = data.get("cognition", {})
        cognition = SimpleNamespace(
            entrypoint=raw.get("entrypoint", ""),
            processors=raw.get("processors", []),
            memory_policy=raw.get("memory_policy", "short"),
        )
    if "safety" in data:
        raw = data.get("safety", {})
        safety = SimpleNamespace(
            block_list=raw.get("block_list", []),
            validators=raw.get("validators", []),
            max_scope=raw.get("max_scope", "read"),
        )
    if "missions" in data:
        raw = data.get("missions", {})
        missions = SimpleNamespace(
            accepts=raw.get("accepts", []),
            generates=raw.get("generates", []),
            autonomy_level=raw.get("autonomy_level", 0),
        )
    if "evolution" in data:
        raw = data.get("evolution", {})
        evolution = SimpleNamespace(
            requires=raw.get("requires", {"xp": 0}),
            unlocks=raw.get("unlocks", []),
        )

    return cognition, safety, missions, evolution


def _is_v1_manifest(data: dict[str, Any]) -> bool:
    required = {
        "id",
        "version",
        "capabilities",
        "inputs",
        "outputs",
        "spawn_policy",
        "constraints",
        "error_modes",
    }
    return required.issubset(set(data.keys()))


def _is_legacy_manifest(data: dict[str, Any]) -> bool:
    required = {"id", "name", "version", "persona", "cognition", "missions", "safety"}
    return required.issubset(set(data.keys()))


def validate_dict(data: dict[str, Any]) -> list[str]:
    if _is_v1_manifest(data):
        return cast(list[str], v1_registry.validate_manifest(data))

    if _is_legacy_manifest(data):
        return []

    return [
        "manifest does not match v1 schema keys or legacy runtime schema keys",
        (
            "expected v1 fields: id, version, capabilities, inputs, outputs, "
            "spawn_policy, constraints, error_modes"
        ),
    ]


def _to_envelope(data: dict[str, Any]) -> _ManifestEnvelope:
    if _is_legacy_manifest(data):
        cognition, safety, missions, evolution = _as_runtime_defaults(data)
        return _ManifestEnvelope(
            payload=dict(data),
            id=str(data["id"]),
            version=str(data["version"]),
            name=str(data.get("name", data["id"])),
            rank=str(data.get("rank", "E")),
            traits=list(data.get("traits", [])),
            capabilities=list(data.get("capabilities", [])),
            spawn_policy=SimpleNamespace(value=str(data.get("spawn_policy", "manual"))),
            cognition=cognition,
            safety=safety,
            missions=missions,
            evolution=evolution,
        )

    cognition, safety, missions, evolution = _as_runtime_defaults(data)
    base_name = str(data["id"]).split("@", 1)[0]
    return _ManifestEnvelope(
        payload=dict(data),
        id=str(data["id"]),
        version=str(data["version"]),
        name=base_name,
        rank="E",
        traits=[],
        capabilities=list(data.get("capabilities", [])),
        spawn_policy=SimpleNamespace(value=str(data.get("spawn_policy", "manual"))),
        cognition=cognition,
        safety=safety,
        missions=missions,
        evolution=evolution,
    )


def register_manifest(data: dict[str, Any]) -> _ManifestEnvelope:
    errors = validate_dict(data)
    if errors:
        raise ValueError("\n".join(errors))

    if _is_v1_manifest(data):
        v1_registry.apply_update(
            manifest_id=str(data["id"]),
            manifest=data,
            actor="register_manifest",
            enforce_ci_gate=False,
        )

    manifest = _to_envelope(data)
    return REGISTRY.register(manifest)


def get_agent(agent_id: str) -> _ManifestEnvelope | None:
    return REGISTRY.get(agent_id)


def list_agents() -> list[_ManifestEnvelope]:
    return REGISTRY.list()


def load_manifest(path: str | Path) -> _ManifestEnvelope:
    payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    return register_manifest(payload)


def load_manifests_from_dir(path: str | Path) -> list[_ManifestEnvelope]:
    loaded: list[_ManifestEnvelope] = []
    for file_path in sorted(Path(path).glob("*.json")):
        loaded.append(load_manifest(file_path))
    return loaded
