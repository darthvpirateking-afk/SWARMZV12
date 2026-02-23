# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
Realms — SWARMZ V3.0 domain partitions.

Realms are isolated operational scopes (e.g., COMBAT, INTEL, SCIENCE)
where missions, swarms, and agents operate independently.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

BUILT_IN_REALMS: list[tuple[str, str]] = [
    ("COMBAT", "Active mission operations and tactical execution"),
    ("INTEL", "Intelligence gathering and analysis pipelines"),
    ("SCIENCE", "Research, experimentation, and learning loops"),
    ("ENTERPRISE", "Business operations, workflows, and integrations"),
    ("CYBER", "Cybersecurity monitoring and defensive operations"),
    ("CLOUD", "Cloud orchestration and infrastructure management"),
    ("ROBOTICS", "Autonomous agents and physical system interfaces"),
    ("LEARNING", "Adaptive learning and model improvement pipelines"),
]


@dataclass
class Realm:
    realm_id: str
    name: str
    description: str
    active: bool = True
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    mission_count: int = 0
    agent_count: int = 0


class RealmRegistry:
    def __init__(self) -> None:
        self._realms: dict[str, Realm] = {}
        for name, desc in BUILT_IN_REALMS:
            rid = name.lower()
            self._realms[rid] = Realm(realm_id=rid, name=name, description=desc)

    def list_realms(self) -> list[dict[str, Any]]:
        return [self._serialize(r) for r in self._realms.values()]

    def get_realm(self, realm_id: str) -> dict[str, Any] | None:
        r = self._realms.get(realm_id.lower())
        return self._serialize(r) if r else None

    def create_realm(self, name: str, description: str) -> dict[str, Any]:
        rid = f"realm-{uuid.uuid4().hex[:8]}"
        r = Realm(realm_id=rid, name=name.upper(), description=description)
        self._realms[rid] = r
        return self._serialize(r)

    @staticmethod
    def _serialize(r: Realm) -> dict[str, Any]:
        return {
            "realm_id": r.realm_id,
            "name": r.name,
            "description": r.description,
            "active": r.active,
            "created_at": r.created_at,
            "mission_count": r.mission_count,
            "agent_count": r.agent_count,
        }


_registry: RealmRegistry | None = None


def get_realm_registry() -> RealmRegistry:
    global _registry
    if _registry is None:
        _registry = RealmRegistry()
    return _registry
