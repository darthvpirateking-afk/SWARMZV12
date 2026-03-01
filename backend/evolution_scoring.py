from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict


class ScoreBand(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class ScoreBreakdown:
    relevance: float
    safety: float
    complexity: float
    impact: float
    confidence: float


@dataclass
class EvolutionScore:
    total: float
    band: ScoreBand
    breakdown: ScoreBreakdown
    rationale: str
    timestamp: str


def clamp(v: float) -> float:
    return max(0.0, min(1.0, v))


def score_proposal(proposal: Dict[str, Any]) -> EvolutionScore:
    ptype = proposal["type"]
    risk = proposal["risk"]
    rationale = proposal.get("rationale", "")

    relevance = 0.7 if "test" in ptype else 0.5
    safety = 1.0 if risk == "low" else 0.6 if risk == "medium" else 0.3
    complexity = 0.3 if risk == "low" else 0.6 if risk == "medium" else 0.9
    impact = 0.8 if ptype in ("plugin", "backend") else 0.5
    confidence = 0.6 if "ensure" in rationale.lower() else 0.5

    total = clamp(
        relevance * 0.25
        + safety * 0.25
        + (1 - complexity) * 0.15
        + impact * 0.25
        + confidence * 0.10
    )

    band = (
        ScoreBand.HIGH
        if total >= 0.66
        else ScoreBand.MEDIUM if total >= 0.33 else ScoreBand.LOW
    )

    return EvolutionScore(
        total=total,
        band=band,
        breakdown=ScoreBreakdown(
            relevance=relevance,
            safety=safety,
            complexity=complexity,
            impact=impact,
            confidence=confidence,
        ),
        rationale="Composite evaluation of relevance, safety, complexity, impact, and confidence.",
        timestamp=datetime.utcnow().isoformat(),
    )
