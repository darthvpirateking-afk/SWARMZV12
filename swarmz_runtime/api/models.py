# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""Consolidated Pydantic request/response models for the SWARMZ API.

All models previously scattered across swarmz_server.py, server.py, and
swarmz_runtime/api/server.py are centralised here.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Task execution (from swarmz_server.py)
# ---------------------------------------------------------------------------
class TaskExecuteRequest(BaseModel):
    task: str
    params: Dict[str, Any] = {}


class TaskExecuteResponse(BaseModel):
    success: bool
    result: Any = None
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# Missions (from swarmz_server.py)
# ---------------------------------------------------------------------------
class MissionCreateRequest(BaseModel):
    goal: str = Field(..., description="Mission goal")
    category: str = Field(..., description="Mission category")
    constraints: Dict[str, Any] = Field(default_factory=dict)
    results: Dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Auth (from swarmz_server.py)
# ---------------------------------------------------------------------------
class LoginRequest(BaseModel):
    username: str
    password: str


# ---------------------------------------------------------------------------
# Dispatch (from server.py – intent/scope/limits variant)
# ---------------------------------------------------------------------------
class DispatchRequest(BaseModel):
    intent: str
    scope: str
    limits: Optional[Dict[str, Any]] = None


# ---------------------------------------------------------------------------
# Mode (from server.py)
# ---------------------------------------------------------------------------
class ModeRequest(BaseModel):
    mode: str


# ---------------------------------------------------------------------------
# Build dispatch (from server.py)
# ---------------------------------------------------------------------------
class BuildDispatchRequest(BaseModel):
    intent: str
    spec: Optional[Dict[str, Any]] = None


# ---------------------------------------------------------------------------
# Sovereign dispatch (from swarmz_runtime/api/server.py)
# ---------------------------------------------------------------------------
class SovereignDispatch(BaseModel):
    intent: str
    scope: Any = Field(default_factory=dict)
    limits: Any = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Pairing (from swarmz_runtime/api/server.py)
# ---------------------------------------------------------------------------
class PairRequest(BaseModel):
    pin: str


# ---------------------------------------------------------------------------
# Mission dispatch (renamed from DispatchRequest in swarmz_runtime/api/server.py)
# ---------------------------------------------------------------------------
class MissionDispatchRequest(BaseModel):
    goal: str
    category: str
    constraints: Dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Command-center models (from swarmz_runtime/api/server.py)
# ---------------------------------------------------------------------------
class AutonomyDialRequest(BaseModel):
    level: int = Field(ge=0, le=100)


class ShadowModeRequest(BaseModel):
    enabled: bool
    lane: str = "mirror"


class EvolutionPromoteRequest(BaseModel):
    partner_id: str
    reason: str = "operator_promotion"


class MarketplacePublishRequest(BaseModel):
    mission_type: str
    title: str
    reward_points: int = Field(ge=0)
    tags: List[str] = Field(default_factory=list)


class OrganismEvolveRequest(BaseModel):
    reason: str = "mission_success"


class LoopTickRequest(BaseModel):
    cycle_label: str = "default"
