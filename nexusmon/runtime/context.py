from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class RuntimeContext:
    workspace: Path
    operator: str = "local-operator"
    env: Dict[str, str] = field(default_factory=dict)
    created_at_utc: str = field(default_factory=_utc_now_iso)


def build_context(
    workspace: Path | str,
    operator: str = "local-operator",
    env: Dict[str, str] | None = None,
) -> RuntimeContext:
    return RuntimeContext(
        workspace=Path(workspace),
        operator=operator,
        env=dict(env or {}),
    )
