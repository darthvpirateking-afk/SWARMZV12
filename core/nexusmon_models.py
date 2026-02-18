"""NEXUSMON Console - Data Models

Pydantic models for the conversational interface layer.
All data is persisted as JSONL for append-only audit trail.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum
from pydantic import BaseModel, Field


# ================================================================
# Enums
# ================================================================

class NexusFormType(str, Enum):
    """Evolution states of operator consciousness in SWARMZ."""
    OPERATOR = "Operator"
    COSMOLOGY = "Cosmology"
    OVERSEER = "Overseer"
    SOVEREIGN = "Sovereign"


class ChatModeType(str, Enum):
    """Response modes for NEXUSMON chat."""
    REFLECT = "Reflect"
    PLAN = "Plan"
    EXPLAIN = "Explain"
    NUDGE = "Nudge"
    MISSION_DRAFT = "MissionDraft"
    STATUS = "Status"


class SuggestedActionType(str, Enum):
    """Types of actions NEXUSMON can suggest."""
    OPEN_MISSION = "OpenMission"
    CREATE_MISSION = "CreateMission"
    VIEW_SHADOW = "ViewShadow"
    VIEW_METRICS = "ViewMetrics"
    VIEW_AUDIT = "ViewAudit"


# ================================================================
# Chat Request/Response
# ================================================================

class ChatContext(BaseModel):
    """UI context for the chat request."""
    mission_id: Optional[str] = None
    screen: str = "None"  # Control | Active | Queue | Metrics | Audit | Shadow | None


class ChatRequest(BaseModel):
    """Request body for POST /chat."""
    operator_id: str
    message: str
    context: ChatContext = Field(default_factory=ChatContext)


class SuggestedAction(BaseModel):
    """A suggested action from NEXUSMON."""
    type: SuggestedActionType
    payload: Dict[str, Any] = Field(default_factory=dict)


class SystemHealth(BaseModel):
    """System health metrics."""
    entropy: float = Field(default=0.5, ge=0.0, le=1.0)
    drift: float = Field(default=0.3, ge=0.0, le=1.0)
    coherence: float = Field(default=0.7, ge=0.0, le=1.0)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class MissionDraft(BaseModel):
    """Mission draft from NEXUSMON."""
    id: Optional[str] = None
    situation: Dict[str, Any] = Field(default_factory=dict)
    goal: str = ""
    constraints: Dict[str, Any] = Field(default_factory=dict)
    evidence: Dict[str, Any] = Field(default_factory=dict)


class StateSnapshot(BaseModel):
    """Current system state snapshot."""
    nexus_form: NexusFormType = NexusFormType.OPERATOR
    system_health: SystemHealth = Field(default_factory=SystemHealth)
    active_missions: int = 0


class ChatReply(BaseModel):
    """Response body for POST /chat."""
    reply: str
    mode: ChatModeType
    suggested_actions: List[SuggestedAction] = Field(default_factory=list)
    mission_draft: Optional[MissionDraft] = None
    state_snapshot: StateSnapshot = Field(default_factory=StateSnapshot)


# ================================================================
# Operator Profile
# ================================================================

class OperatorProfile(BaseModel):
    """Profile of an operator in SWARMZ."""
    operator_id: str
    username: str = ""
    risk_posture: str = "balanced"  # conservative | balanced | aggressive
    drift_score: float = Field(default=0.0, ge=0.0, le=1.0)
    fatigue: float = Field(default=0.0, ge=0.0, le=1.0)
    friction_patterns: List[str] = Field(default_factory=list)
    preferences: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "operator_id": "op-123",
                "username": "regan",
                "risk_posture": "balanced",
                "drift_score": 0.3,
                "fatigue": 0.2,
                "friction_patterns": ["avoids_complex_missions", "prefers_explanations"],
            }
        }


# ================================================================
# Persona
# ================================================================

class PersonaStyle(BaseModel):
    """Tone parameters for NEXUSMON persona."""
    warmth: float = Field(default=0.7, ge=0.0, le=1.0)
    directness: float = Field(default=0.8, ge=0.0, le=1.0)
    abstraction: float = Field(default=0.4, ge=0.0, le=1.0)
    metaphor: float = Field(default=0.5, ge=0.0, le=1.0)


class PersonaConstraints(BaseModel):
    """Hard behavioral limits for NEXUSMON."""
    no_emotional_dependency: bool = True
    no_flattery: bool = True
    no_deception: bool = True
    no_human_impersonation: bool = True
    no_exclusivity_promises: bool = True


class Persona(BaseModel):
    """NEXUSMON persona (evolution-aware)."""
    name: str = "NEXUSMON"
    form: NexusFormType = NexusFormType.OPERATOR
    style: PersonaStyle = Field(default_factory=PersonaStyle)
    constraints: PersonaConstraints = Field(default_factory=PersonaConstraints)
    description: str = ""


# ================================================================
# Conversation Storage
# ================================================================

class ConversationTurn(BaseModel):
    """A single turn in the conversation."""
    id: str
    operator_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    message: str
    reply: str
    mode: ChatModeType
    tags: List[str] = Field(default_factory=list)


class OperatorMemory(BaseModel):
    """Long-term operator memory (compressed patterns)."""
    operator_id: str
    summary: str
    last_updated_at: datetime = Field(default_factory=datetime.utcnow)
    tags: List[str] = Field(default_factory=list)
    patterns: Dict[str, Any] = Field(default_factory=dict)


# ================================================================
# NexusForm (Evolution State)
# ================================================================

class NexusForm(BaseModel):
    """Current evolution state of operator."""
    operator_id: str
    current_form: NexusFormType = NexusFormType.OPERATOR
    transition_evidence: List[Dict[str, Any]] = Field(default_factory=list)
    coherence_score: float = Field(default=0.7, ge=0.0, le=1.0)
    last_evolved_at: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "operator_id": "op-123",
                "current_form": "Operator",
                "transition_evidence": [
                    {"type": "mission_mastery", "count": 5}
                ],
                "coherence_score": 0.85
            }
        }


# ================================================================
# Conversation Context (Internal)
# ================================================================

class ConversationContext(BaseModel):
    """Internal context used by conversation engine."""
    operator: OperatorProfile
    nexus_form: NexusForm
    missions: List[Dict[str, Any]] = Field(default_factory=list)
    health: SystemHealth = Field(default_factory=SystemHealth)
    history: List[ConversationTurn] = Field(default_factory=list)
    ui_context: ChatContext = Field(default_factory=ChatContext)
    persona: Optional[Persona] = None

    class Config:
        arbitrary_types_allowed = True


# ================================================================
# Mission Schema (for integration)
# ================================================================

class Mission(BaseModel):
    """Mission object."""
    mission_id: str
    goal: str
    category: str = ""
    status: str = "PENDING"  # PENDING | RUNNING | COMPLETED | FAILED
    created_at: datetime = Field(default_factory=datetime.utcnow)
    constraints: Dict[str, Any] = Field(default_factory=dict)
    results: Dict[str, Any] = Field(default_factory=dict)
    outcome: Optional[str] = None


# ================================================================
# Audit Event
# ================================================================

class AuditEvent(BaseModel):
    """Audit event for system transparency."""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    event_type: str  # mission_dispatched | chat_turn | evolution_change | etc.
    operator_id: Optional[str] = None
    mission_id: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "2026-02-19T10:30:00Z",
                "event_type": "chat_turn",
                "operator_id": "op-123",
                "details": {
                    "message": "Help me plan a mission",
                    "reply": "...",
                    "mode": "Plan"
                }
            }
        }
