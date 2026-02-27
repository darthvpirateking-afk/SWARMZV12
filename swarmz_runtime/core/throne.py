# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
Throne Layer — SWARMZ V3.0 sovereign authority layer.

Holds the operator's identity, system constitution, and decree ledger.
All sub-systems defer to Throne for final authority on policy decisions.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

THRONE_IDENTITY = "SOVEREIGN_OPERATOR"

THRONE_CONSTITUTION = [
    "All systems serve the Operator's intent and protection.",
    "Transparency and auditability are non-negotiable.",
    "Minimal action under uncertainty.",
    "Sovereignty cannot be delegated without operator consent.",
    "The Throne Ledger is append-only and immutable.",
]


@dataclass
class Decree:
    decree_id: str
    title: str
    body: str
    issued_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    authority_level: str = "SOVEREIGN"
    active: bool = True


class ThroneLayer:
    """Sovereign authority layer. Issues decrees, holds constitution, owns identity."""

    def __init__(self) -> None:
        self._decrees: list[Decree] = []
        self._identity = THRONE_IDENTITY
        self._constitution = list(THRONE_CONSTITUTION)

    @property
    def identity(self) -> str:
        return self._identity

    @property
    def constitution(self) -> list[str]:
        return list(self._constitution)

    def issue_decree(
        self, title: str, body: str, authority_level: str = "SOVEREIGN"
    ) -> Decree:
        decree = Decree(
            decree_id=f"DECREE-{uuid.uuid4().hex[:8].upper()}",
            title=title,
            body=body,
            authority_level=authority_level,
        )
        self._decrees.append(decree)
        return decree

    def get_state(self) -> dict[str, Any]:
        return {
            "identity": self._identity,
            "constitution": self._constitution,
            "active_decrees": len([d for d in self._decrees if d.active]),
            "total_decrees": len(self._decrees),
            "status": "SOVEREIGN",
        }

    def get_ledger(self) -> list[dict[str, Any]]:
        return [
            {
                "decree_id": d.decree_id,
                "title": d.title,
                "body": d.body,
                "issued_at": d.issued_at,
                "authority_level": d.authority_level,
                "active": d.active,
            }
            for d in self._decrees
        ]


_throne: ThroneLayer | None = None


def get_throne() -> ThroneLayer:
    global _throne
    if _throne is None:
        _throne = ThroneLayer()
    return _throne
