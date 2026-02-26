"""NEXUSMON – AI Agent Manifest Loader (v1.0)

Validates, loads, and registers agent manifests against the canonical
genome schema at config/agent_manifest.schema.json.

Public surface
--------------
    load_manifest(path)             -> AgentManifest
    register_manifest(data: dict)   -> AgentManifest
    get_agent(agent_id)             -> AgentManifest | None
    list_agents()                   -> list[AgentManifest]
    validate_dict(data: dict)       -> list[str]   (errors; empty = valid)
    REGISTRY                        -> ManifestRegistry singleton
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Schema path (resolved relative to this file)
# ---------------------------------------------------------------------------
_SCHEMA_PATH = Path(__file__).resolve().parent.parent / "config" / "agent_manifest.schema.json"

# ---------------------------------------------------------------------------
# Optional jsonschema validation (graceful degradation if not installed)
# ---------------------------------------------------------------------------
try:
    import jsonschema  # type: ignore

    def _load_schema() -> Dict[str, Any]:
        with open(_SCHEMA_PATH, encoding="utf-8") as fh:
            return json.load(fh)

    def validate_dict(data: Dict[str, Any]) -> List[str]:
        """Return a list of validation error strings (empty list = valid)."""
        schema = _load_schema()
        validator = jsonschema.Draft202012Validator(schema)
        return [e.message for e in validator.iter_errors(data)]

except ImportError:
    jsonschema = None  # type: ignore

    def validate_dict(data: Dict[str, Any]) -> List[str]:  # noqa: F811
        """Fallback: light structural check without jsonschema library."""
        errors: List[str] = []
        required = ["id", "name", "version", "persona", "cognition", "missions", "safety"]
        for field in required:
            if field not in data:
                errors.append(f"Missing required field: '{field}'")
        return errors


# ---------------------------------------------------------------------------
# Pydantic models (mirror the JSON Schema for in-process type safety)
# ---------------------------------------------------------------------------

class PersonaModel(BaseModel):
    summary: str
    directives: List[str]
    constraints: List[str]


class CognitionModel(BaseModel):
    entrypoint: str
    processors: List[str] = Field(default_factory=list)
    memory_policy: Optional[str] = None  # none|short|long|episodic


class MissionsModel(BaseModel):
    accepts: List[str]
    generates: List[str]
    autonomy_level: int = Field(ge=0, le=3)


class RateLimitsModel(BaseModel):
    calls_per_min: Optional[float] = None
    missions_per_hour: Optional[float] = None


class SafetyModel(BaseModel):
    validators: List[str]
    max_scope: str  # none|read|write|system
    rate_limits: Optional[RateLimitsModel] = None


class EvolutionRequiresModel(BaseModel):
    xp: Optional[float] = None
    rank: Optional[str] = None
    traits: List[str] = Field(default_factory=list)


class EvolutionModel(BaseModel):
    requires: Optional[EvolutionRequiresModel] = None
    unlocks: List[str] = Field(default_factory=list)


class UIModel(BaseModel):
    icon: Optional[str] = None
    color: Optional[str] = None
    panel: Optional[str] = None  # swarm|factory|missions|chronicle|custom


class AgentManifest(BaseModel):
    """Fully validated NEXUSMON agent genome."""

    schema_version: str = "1.0.0"
    id: str
    name: str
    version: str
    rank: Optional[str] = None  # E|D|C|B|A|S
    traits: List[str] = Field(default_factory=list)
    persona: PersonaModel
    cognition: CognitionModel
    missions: MissionsModel
    safety: SafetyModel
    evolution: Optional[EvolutionModel] = None
    ui: Optional[UIModel] = None

    model_config = {"extra": "ignore"}

    @field_validator("version")
    @classmethod
    def _semver(cls, v: str) -> str:
        parts = v.split(".")
        if len(parts) != 3 or not all(p.isdigit() for p in parts):
            raise ValueError(f"version must be MAJOR.MINOR.PATCH, got '{v}'")
        return v

    @field_validator("rank")
    @classmethod
    def _rank(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ("E", "D", "C", "B", "A", "S"):
            raise ValueError(f"rank must be one of E D C B A S, got '{v}'")
        return v

    # ------------------------------------------------------------------ #
    # Convenience helpers                                                  #
    # ------------------------------------------------------------------ #

    @property
    def autonomy_label(self) -> str:
        labels = ["Manual", "Assisted", "Semi-Auto", "Full-Auto"]
        return labels[self.missions.autonomy_level]

    @property
    def rank_color(self) -> str:
        colors = {
            "E": "#445566",
            "D": "#00aaff",
            "C": "#00ffaa",
            "B": "#ffaa00",
            "A": "#ff6b00",
            "S": "#ff44aa",
        }
        return colors.get(self.rank or "E", "#445566")

    @property
    def dot_color(self) -> str:
        """UI dot color: manifest ui.color override first, then rank default."""
        if self.ui and self.ui.color:
            return self.ui.color
        return self.rank_color

    @property
    def xp_required(self) -> Optional[float]:
        if self.evolution and self.evolution.requires:
            return self.evolution.requires.xp
        return None

    def to_cockpit_card(self) -> Dict[str, Any]:
        """Serialise fields the cockpit unit card needs in a single dict."""
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "rank": self.rank or "E",
            "rank_color": self.rank_color,
            "dot_color": self.dot_color,
            "autonomy_level": self.missions.autonomy_level,
            "autonomy_label": self.autonomy_label,
            "traits": self.traits,
            "panel": (self.ui.panel if self.ui else None) or "swarm",
            "icon": (self.ui.icon if self.ui else None) or "🤖",
            "xp_required": self.xp_required,
            "max_scope": self.safety.max_scope,
        }


# ---------------------------------------------------------------------------
# Registry – in-memory singleton
# ---------------------------------------------------------------------------

class ManifestRegistry:
    """Thread-safe (read) registry of loaded agent manifests."""

    def __init__(self) -> None:
        self._store: Dict[str, AgentManifest] = {}

    # ------------------------------------------------------------------ #

    def register(self, manifest: AgentManifest) -> AgentManifest:
        self._store[manifest.id] = manifest
        logger.info("Registered agent manifest: %s v%s (rank=%s)", manifest.id, manifest.version, manifest.rank)
        return manifest

    def get(self, agent_id: str) -> Optional[AgentManifest]:
        return self._store.get(agent_id)

    def list(self) -> List[AgentManifest]:
        return list(self._store.values())

    def remove(self, agent_id: str) -> bool:
        if agent_id in self._store:
            del self._store[agent_id]
            return True
        return False

    def clear(self) -> None:
        self._store.clear()

    def __len__(self) -> int:
        return len(self._store)

    def __repr__(self) -> str:
        return f"<ManifestRegistry agents={list(self._store.keys())}>"


REGISTRY = ManifestRegistry()


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def load_manifest(path: str | Path) -> AgentManifest:
    """Load and validate a manifest JSON file from disk.

    Raises
    ------
    FileNotFoundError   – path does not exist
    ValueError          – schema validation failed
    pydantic.ValidationError – field-level type errors
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Manifest not found: {path}")

    with open(path, encoding="utf-8") as fh:
        data: Dict[str, Any] = json.load(fh)

    errors = validate_dict(data)
    if errors:
        raise ValueError("Manifest schema validation failed:\n" + "\n".join(f"  • {e}" for e in errors))

    manifest = AgentManifest(**data)
    REGISTRY.register(manifest)
    return manifest


def register_manifest(data: Dict[str, Any]) -> AgentManifest:
    """Validate and register a manifest from a dict (e.g. parsed from API body).

    Raises
    ------
    ValueError          – schema validation failed
    pydantic.ValidationError – field-level type errors
    """
    errors = validate_dict(data)
    if errors:
        raise ValueError("Manifest schema validation failed:\n" + "\n".join(f"  • {e}" for e in errors))

    manifest = AgentManifest(**data)
    REGISTRY.register(manifest)
    return manifest


def get_agent(agent_id: str) -> Optional[AgentManifest]:
    """Retrieve a registered manifest by id."""
    return REGISTRY.get(agent_id)


def list_agents() -> List[AgentManifest]:
    """Return all registered manifests."""
    return REGISTRY.list()


def load_manifests_from_dir(directory: str | Path) -> List[AgentManifest]:
    """Scan a directory for *.manifest.json files and load them all.

    Returns only successfully loaded manifests; errors are logged as warnings.
    """
    directory = Path(directory)
    loaded: List[AgentManifest] = []
    for manifest_file in sorted(directory.glob("*.manifest.json")):
        try:
            loaded.append(load_manifest(manifest_file))
        except Exception as exc:  # noqa: BLE001
            logger.warning("Skipped %s: %s", manifest_file.name, exc)
    return loaded
