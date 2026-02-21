# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""Repository layer — typed data-access methods over SQLAlchemy sessions.

Each repository wraps a single ORM model and exposes CRUD + query methods.
All methods accept an explicit ``Session`` so they can be used both as
FastAPI dependencies and from synchronous engine code.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from swarmz_runtime.storage.orm_models import (
    AuditEntryModel,
    CommandCenterStateModel,
    MissionModel,
    RuneModel,
    RunModel,
    SystemStateModel,
)


# ---------------------------------------------------------------------------
# Missions
# ---------------------------------------------------------------------------
class MissionRepository:
    @staticmethod
    def create(session: Session, *, mission_id: str, goal: str, category: str = "forge",
               constraints: dict | None = None, results: dict | None = None,
               intent: str | None = None, scope: dict | None = None,
               limits: dict | None = None, status: str = "pending") -> MissionModel:
        m = MissionModel(
            id=mission_id,
            goal=goal,
            category=category,
            constraints=constraints or {},
            results=results or {},
            status=status,
            intent=intent,
            scope=scope,
            limits=limits,
        )
        session.add(m)
        session.flush()
        return m

    @staticmethod
    def get(session: Session, mission_id: str) -> Optional[MissionModel]:
        return session.get(MissionModel, mission_id)

    @staticmethod
    def list_all(session: Session, *, status: str | None = None,
                 limit: int = 500) -> List[MissionModel]:
        q = session.query(MissionModel)
        if status:
            q = q.filter(MissionModel.status == status)
        return q.order_by(desc(MissionModel.created_at)).limit(limit).all()

    @staticmethod
    def update(session: Session, mission_id: str, updates: Dict[str, Any]) -> Optional[MissionModel]:
        m = session.get(MissionModel, mission_id)
        if not m:
            return None
        for k, v in updates.items():
            if hasattr(m, k):
                setattr(m, k, v)
        m.updated_at = datetime.now(timezone.utc)
        session.flush()
        return m

    @staticmethod
    def count_by_status(session: Session) -> Dict[str, int]:
        rows = (
            session.query(MissionModel.status, func.count(MissionModel.id))
            .group_by(MissionModel.status)
            .all()
        )
        return {status: count for status, count in rows}


# ---------------------------------------------------------------------------
# Audit
# ---------------------------------------------------------------------------
class AuditRepository:
    @staticmethod
    def log(session: Session, *, event_type: str, mission_id: str | None = None,
            details: dict | None = None, visibility: str = "visible") -> AuditEntryModel:
        entry = AuditEntryModel(
            event_type=event_type,
            mission_id=mission_id,
            details=details or {},
            visibility=visibility,
        )
        session.add(entry)
        session.flush()
        return entry

    @staticmethod
    def tail(session: Session, limit: int = 20) -> List[AuditEntryModel]:
        return (
            session.query(AuditEntryModel)
            .order_by(desc(AuditEntryModel.timestamp))
            .limit(limit)
            .all()
        )


# ---------------------------------------------------------------------------
# Runes
# ---------------------------------------------------------------------------
class RuneRepository:
    @staticmethod
    def save(session: Session, *, rune_id: str, template: dict,
             confidence: float = 0.0, success_count: int = 0) -> RuneModel:
        existing = session.get(RuneModel, rune_id)
        if existing:
            existing.template = template
            existing.confidence = confidence
            existing.success_count = success_count
            existing.last_used = datetime.now(timezone.utc)
            session.flush()
            return existing
        r = RuneModel(id=rune_id, template=template, confidence=confidence,
                      success_count=success_count)
        session.add(r)
        session.flush()
        return r

    @staticmethod
    def get(session: Session, rune_id: str) -> Optional[RuneModel]:
        return session.get(RuneModel, rune_id)

    @staticmethod
    def list_all(session: Session) -> List[RuneModel]:
        return session.query(RuneModel).all()


# ---------------------------------------------------------------------------
# System state (single-row)
# ---------------------------------------------------------------------------
class SystemStateRepository:
    @staticmethod
    def get_or_create(session: Session) -> SystemStateModel:
        row = session.get(SystemStateModel, 1)
        if not row:
            row = SystemStateModel(id=1)
            session.add(row)
            session.flush()
        return row

    @staticmethod
    def update(session: Session, **fields) -> SystemStateModel:
        row = SystemStateRepository.get_or_create(session)
        for k, v in fields.items():
            if hasattr(row, k):
                setattr(row, k, v)
        row.version = (row.version or 0) + 1
        session.flush()
        return row


# ---------------------------------------------------------------------------
# Command-center state (single-row JSON blob)
# ---------------------------------------------------------------------------
class CommandCenterRepository:
    @staticmethod
    def read(session: Session) -> dict:
        row = session.get(CommandCenterStateModel, 1)
        if not row:
            return {}
        return row.state_json or {}

    @staticmethod
    def write(session: Session, state: dict) -> None:
        row = session.get(CommandCenterStateModel, 1)
        if not row:
            row = CommandCenterStateModel(id=1, state_json=state)
            session.add(row)
        else:
            row.state_json = state
        session.flush()


# ---------------------------------------------------------------------------
# Runs
# ---------------------------------------------------------------------------
class RunRepository:
    @staticmethod
    def create(session: Session, *, mission_id: str | None = None,
               status: str = "pending") -> RunModel:
        run = RunModel(mission_id=mission_id, status=status)
        session.add(run)
        session.flush()
        return run

    @staticmethod
    def tail(session: Session, limit: int = 20) -> List[RunModel]:
        return (
            session.query(RunModel)
            .order_by(desc(RunModel.started_at))
            .limit(limit)
            .all()
        )
