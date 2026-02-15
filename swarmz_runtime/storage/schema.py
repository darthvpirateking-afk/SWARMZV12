from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class MissionCategory(str, Enum):
    COIN = "coin"
    FORGE = "forge"
    LIBRARY = "library"
    SANCTUARY = "sanctuary"


class MissionStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    SUSPENDED = "suspended"


class VisibilityLevel(str, Enum):
    DIM = "dim"
    VISIBLE = "visible"
    BRIGHT = "bright"
    ULTRAVIOLET = "ultraviolet"


class Mission(BaseModel):
    id: str
    goal: str
    category: MissionCategory
    constraints: Dict[str, Any] = Field(default_factory=dict)
    expiry: Optional[datetime] = None
    status: MissionStatus = MissionStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    leverage_score: float = 0.0
    revisit_interval: int = 3600


class CrossLayerScores(BaseModel):
    compute_cost: float
    maintainability: float
    attention: float
    economic_value: float
    trust: float
    prediction_confidence: float


class TransactionValidation(BaseModel):
    safe: bool
    borderline: bool
    failing: bool
    requires_approval: bool
    scores: CrossLayerScores


class Omen(BaseModel):
    pattern: str
    frequency: int
    threshold: int
    action: str


class Rune(BaseModel):
    id: str
    template: Dict[str, Any]
    confidence: float
    success_count: int
    created_at: datetime
    last_used: datetime


class AuditEntry(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.now)
    event_type: str
    mission_id: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    visibility: VisibilityLevel = VisibilityLevel.VISIBLE


class Prophecy(BaseModel):
    failure_signature: str
    likelihood: float
    warning: str
    recommended_action: str


class MaintenanceTask(BaseModel):
    module: str
    complexity_score: float
    scheduled_at: datetime
    reason: str
