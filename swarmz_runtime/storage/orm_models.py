# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""SQLAlchemy ORM models for SWARMZ persistence.

Maps the existing Pydantic schemas (swarmz_runtime.storage.schema) to
relational tables. Supports PostgreSQL and SQLite.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from swarmz_runtime.storage.database import Base


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _new_id() -> str:
    return uuid.uuid4().hex[:12]


# ---------------------------------------------------------------------------
# Missions
# ---------------------------------------------------------------------------
class MissionModel(Base):
    __tablename__ = "missions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=_new_id)
    goal: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(32), nullable=False, default="forge")
    constraints: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    leverage_score: Mapped[float] = mapped_column(Float, default=0.0)
    revisit_interval: Mapped[int] = mapped_column(Integer, default=3600)
    operator_public_key: Mapped[str | None] = mapped_column(String(256), nullable=True)
    results: Mapped[dict] = mapped_column(JSON, default=dict)
    intent: Mapped[str | None] = mapped_column(Text, nullable=True)
    scope: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    limits: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now, onupdate=_utc_now)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_missions_status", "status"),
        Index("ix_missions_category", "category"),
        Index("ix_missions_created", "created_at"),
    )


# ---------------------------------------------------------------------------
# Audit log
# ---------------------------------------------------------------------------
class AuditEntryModel(Base):
    __tablename__ = "audit_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now, index=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    mission_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    visibility: Mapped[str] = mapped_column(String(20), default="visible")


# ---------------------------------------------------------------------------
# Runes (pattern templates)
# ---------------------------------------------------------------------------
class RuneModel(Base):
    __tablename__ = "runes"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=_new_id)
    template: Mapped[dict] = mapped_column(JSON, default=dict)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    success_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)
    last_used: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)


# ---------------------------------------------------------------------------
# System state (single-row table for runtime config persistence)
# ---------------------------------------------------------------------------
class SystemStateModel(Base):
    __tablename__ = "system_state"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    mode: Mapped[str] = mapped_column(String(20), default="COMPANION")
    active_missions: Mapped[int] = mapped_column(Integer, default=0)
    pattern_counters: Mapped[dict] = mapped_column(JSON, default=dict)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now, onupdate=_utc_now)
    version: Mapped[int] = mapped_column(Integer, default=1)


# ---------------------------------------------------------------------------
# Command-center state (single-row, persists autonomy/shadow/evolution)
# ---------------------------------------------------------------------------
class CommandCenterStateModel(Base):
    __tablename__ = "command_center_state"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    state_json: Mapped[dict] = mapped_column(JSON, default=dict)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now, onupdate=_utc_now)


# ---------------------------------------------------------------------------
# Runs (mission execution records)
# ---------------------------------------------------------------------------
class RunModel(Base):
    __tablename__ = "runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    mission_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    result: Mapped[dict] = mapped_column(JSON, default=dict)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utc_now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
