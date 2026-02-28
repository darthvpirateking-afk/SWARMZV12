from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class RefactorHint:
    id: str
    target: str
    kind: str
    suggestion: str


HINTS: List[RefactorHint] = []


def analyze_structure() -> List[RefactorHint]:
    hints = [
        RefactorHint(
            id="hint-1",
            target="mission_engine",
            kind="module",
            suggestion="Consider splitting mission_engine into planner + executor modules.",
        )
    ]
    HINTS.clear()
    HINTS.extend(hints)
    return HINTS
