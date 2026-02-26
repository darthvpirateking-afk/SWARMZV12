# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""nexusmon/oig/models.py -- Pydantic data models for the Operator Identity Graph.

Every model that represents an extracted fact MUST include a confidence field (0.0-1.0).
confidence=0.9+  : explicit statement ("My name is X", "I want to build Y")
confidence=0.5-0.8: strong inference from context
confidence=0.3-0.5: weak signal (indirect language, topic proximity)
confidence=<0.3  : speculative
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field


# ── Base ─────────────────────────────────────────────────────────────────────


class OIGFact(BaseModel):
    """Base class for all facts stored in the temporal graph.

    Every concrete fact MUST inherit from this and carry a confidence score.
    confidence determines retrieval priority and context inclusion threshold.
    source documents the extraction path for auditability.
    """

    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description=(
            "Extraction confidence. "
            "0.9+ = explicit statement, "
            "0.5-0.8 = strong inference, "
            "0.3-0.5 = weak signal, "
            "<0.3 = speculative"
        ),
    )
    source: str = Field(
        default="behavioral_inference",
        description=(
            "Extraction origin: explicit_statement | behavioral_inference | "
            "correction | pattern_detection | manual_input"
        ),
    )


# ── Communication & Thinking Style ───────────────────────────────────────────


class CommunicationStyle(BaseModel):
    verbosity: float = Field(0.5, ge=0.0, le=1.0)       # 0.0 terse → 1.0 expansive
    formality: float = Field(0.5, ge=0.0, le=1.0)        # 0.0 casual → 1.0 formal
    directness: float = Field(0.5, ge=0.0, le=1.0)       # 0.0 indirect → 1.0 blunt
    humor_affinity: float = Field(0.5, ge=0.0, le=1.0)   # 0.0 serious → 1.0 playful
    preferred_feedback: str = Field(
        "direct",
        description="blunt | diplomatic | socratic | challenging",
    )


class ThinkingStyle(BaseModel):
    approach: list[str] = Field(
        default_factory=list,
        description="visual, verbal, systems, intuitive, analytical",
    )
    decision_pattern: str = Field(
        "iterative",
        description="fast-decisive | deliberate | iterative | consensus-seeking",
    )
    risk_tolerance: float = Field(0.5, ge=0.0, le=1.0)
    abstraction_preference: float = Field(
        0.5, ge=0.0, le=1.0,
        description="0.0 concrete → 1.0 abstract",
    )


# ── Operator Identity ─────────────────────────────────────────────────────────


class OperatorIdentity(BaseModel):
    """Core identity of the operator. Emergent — discovered, not assigned."""

    name: Optional[str] = None
    aliases: list[str] = Field(default_factory=list)
    archetype: Optional[str] = Field(
        None,
        description="Emergent archetype discovered through behavior, not assigned",
    )
    communication_style: CommunicationStyle = Field(
        default_factory=CommunicationStyle
    )
    thinking_style: ThinkingStyle = Field(default_factory=ThinkingStyle)


# ── Values ────────────────────────────────────────────────────────────────────


class ValueEntry(OIGFact):
    value: str
    category: str = Field(
        "observed",
        description="stated | observed",
    )
    evidence: list[str] = Field(default_factory=list)


# ── Emotional State ───────────────────────────────────────────────────────────


class EmotionalState(BaseModel):
    baseline_energy: float = Field(0.5, ge=0.0, le=1.0)
    current_mood: str = "neutral"
    estimated_confidence: float = Field(
        0.5, ge=0.0, le=1.0,
        description="How confident NEXUSMON is in this emotional read",
    )
    evidence: list[str] = Field(default_factory=list)
    last_updated: datetime = Field(default_factory=datetime.utcnow)


# ── Expertise ─────────────────────────────────────────────────────────────────


class ExpertiseDomain(OIGFact):
    domain: str
    depth: float = Field(0.0, ge=0.0, le=1.0, description="0.0 novice → 1.0 expert")
    growth_trajectory: str = Field(
        "steady",
        description="accelerating | steady | plateaued | declining",
    )
    evidence: list[str] = Field(default_factory=list)


# ── Goals ─────────────────────────────────────────────────────────────────────


class GoalEntry(OIGFact):
    id: str = Field(default_factory=lambda: str(uuid4()))
    description: str
    category: str = Field(
        "technical",
        description="professional | personal | creative | technical | philosophical",
    )
    priority: float = Field(0.5, ge=0.0, le=1.0)
    progress: float = Field(0.0, ge=0.0, le=1.0)
    blockers: list[str] = Field(default_factory=list)
    nexusmon_role: str = Field(
        "",
        description="How NEXUSMON specifically helps with this goal",
    )
    status: str = Field(
        "active",
        description="active | dormant | completed | abandoned",
    )


# ── Bond Metrics ──────────────────────────────────────────────────────────────


class BondMetrics(BaseModel):
    """Computed bond state — never assigned, always derived from graph data."""

    trust_level: float = Field(
        0.1, ge=0.0, le=1.0,
        description=(
            "Computed trust: base=0.1 "
            "+ time_component(max 0.2) "
            "+ shared_experience(max 0.25) "
            "+ corrections_learned(max 0.2) "
            "+ conflict_resolution(max 0.15)"
        ),
    )
    bond_age_days: int = 0
    shared_victories: int = 0
    shared_failures: int = 0
    corrections_received: int = 0
    corrections_learned_from: int = 0
    disagreements: int = 0
    inside_references: list[str] = Field(default_factory=list)


# ── Temporal Edge ─────────────────────────────────────────────────────────────


class OIGEdge(BaseModel):
    """A single temporal fact edge in the knowledge graph.

    The temporal model follows Graphiti's bi-temporal spec:
    - t_valid_from/t_valid_to: when the fact was true in reality
    - t_ingested: when NEXUSMON learned this fact
    - t_valid_to=None means the fact is still valid (current)
    """

    id: str = Field(default_factory=lambda: str(uuid4()))
    subject_id: str
    predicate: str
    object_id: str
    t_valid_from: datetime
    t_valid_to: Optional[datetime] = None
    t_ingested: datetime = Field(default_factory=datetime.utcnow)
    confidence: float = Field(0.5, ge=0.0, le=1.0)
    source: str = "behavioral_inference"
    fact_type: str = Field(
        "general",
        description=(
            "general | goal | preference | expertise | emotion | "
            "correction | value | pattern | identity"
        ),
    )
    metadata: dict = Field(default_factory=dict)


# ── Patterns ──────────────────────────────────────────────────────────────────


class PatternEntry(BaseModel):
    """A detected behavioral pattern. Higher occurrence_count = stronger signal."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    operator_id: str
    pattern_type: str = Field(
        description="behavioral | conversational | mission | energy | decision"
    )
    description: str
    evidence: list[str] = Field(default_factory=list)
    first_seen: datetime = Field(default_factory=datetime.utcnow)
    last_seen: datetime = Field(default_factory=datetime.utcnow)
    occurrence_count: int = 1
    confidence: float = Field(0.5, ge=0.0, le=1.0)


# ── Epochs ────────────────────────────────────────────────────────────────────


class EpochEntry(BaseModel):
    """A named period in the operator-NEXUSMON relationship.

    Epochs are auto-detected when enough facts change within a time window.
    They can also be created manually via the API.
    The current epoch has end=None.
    """

    id: str = Field(default_factory=lambda: str(uuid4()))
    operator_id: str
    name: str = Field(
        description='e.g., "The Infrastructure Phase", "The Vision Sprint"'
    )
    start: datetime = Field(default_factory=datetime.utcnow)
    end: Optional[datetime] = Field(
        None,
        description="None = current epoch",
    )
    defining_characteristic: str = ""
    missions_completed: int = 0
    fact_changes: int = 0
    mood_signature: str = "neutral"
    growth_areas: list[str] = Field(default_factory=list)


# ── Extraction Signal (internal) ──────────────────────────────────────────────


class ExtractedSignal(BaseModel):
    """Internal model for a single signal extracted from an exchange.

    Used by the ingestion pipeline before writing to the graph.
    """

    signal_type: str = Field(
        description="goal | preference | correction | emotion | expertise | value | identity"
    )
    description: str
    confidence: float = Field(ge=0.0, le=1.0)
    source: str = "behavioral_inference"
    evidence: str = ""
    metadata: dict = Field(default_factory=dict)
