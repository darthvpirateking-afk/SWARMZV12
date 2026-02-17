# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from addons.config_ext import get_config
from swarmz_runtime.core import infra_metrics
from swarmz_runtime.core.infra_autoscale import compute_autoscale_recommendations
from swarmz_runtime.core.infra_backup import compute_backup_plan
from swarmz_runtime.core.infra_missions import emit_infra_missions
from swarmz_runtime.storage.infra_state import load_infra_events, load_infra_state


router = APIRouter(prefix="/v1/infra", tags=["infra"])


def _infra_enabled() -> bool:
    try:
        cfg = get_config()
    except Exception:
        return False
    return bool(cfg.get("infra_orchestrator_enabled"))


class InfraMetricSample(BaseModel):
    node_id: str = Field(..., min_length=1)
    cpu: Optional[float] = None
    memory: Optional[float] = None
    gpu: Optional[float] = None
    disk: Optional[float] = None
    net_rx: Optional[float] = None
    net_tx: Optional[float] = None
    ts: Optional[str] = None
    # Free-form additional attributes; not used in aggregation but stored.
    extra: Dict[str, Any] = Field(default_factory=dict)


@router.post("/metrics")
def ingest_metrics(sample: InfraMetricSample):
    """Ingest a single infra metrics sample into the append-only log."""

    if not _infra_enabled():
        raise HTTPException(status_code=404, detail="infra orchestrator disabled")

    payload = sample.dict()
    # Flatten extra into the top-level sample for storage, but keep
    # reserved keys intact.
    extra = payload.pop("extra", {}) or {}
    merged: Dict[str, Any] = {**payload, **extra}
    infra_metrics.record_infra_metrics(merged)
    return {"ok": True}


@router.get("/overview")
def infra_overview(limit: int = 500):
    """Return a coarse infra overview derived from recent metrics."""

    if not _infra_enabled():
        raise HTTPException(status_code=404, detail="infra orchestrator disabled")

    overview = infra_metrics.build_infra_overview(limit=limit)
    return overview


@router.get("/events")
def infra_events(limit: int = 100):
    """Return the tail of raw infra events for debugging/inspection."""

    if not _infra_enabled():
        raise HTTPException(status_code=404, detail="infra orchestrator disabled")

    limit = max(1, min(limit, 1000))
    events = load_infra_events(limit=limit)
    return {"events": events, "count": len(events)}


@router.get("/state")
def infra_state():
    """Return the last materialized infra state snapshot, if any."""

    if not _infra_enabled():
        raise HTTPException(status_code=404, detail="infra orchestrator disabled")

    state = load_infra_state()
    return {"state": state}


@router.get("/backup_plan")
def infra_backup_plan():
    """Return a conservative backup/disaster-recovery recommendation.

    This endpoint only inspects the current infra_state snapshot and
    suggests a schedule and priorities; it does not create or run
    actual backup jobs.
    """

    if not _infra_enabled():
        raise HTTPException(status_code=404, detail="infra orchestrator disabled")

    state = load_infra_state()
    plan = compute_backup_plan(state)
    return plan


@router.post("/plan_missions")
def infra_plan_missions(limit: int = 500, target_cpu: float = 0.6, max_cpu: float = 0.85, min_cpu: float = 0.15):
    """Emit simulation-only missions for infra autoscale/backup plans.

    This translates the current autoscale and backup recommendations
    into standard SWARMZ missions in missions.jsonl without executing
    any real infrastructure changes.
    """

    if not _infra_enabled():
        raise HTTPException(status_code=404, detail="infra orchestrator disabled")

    overview = infra_metrics.build_infra_overview(limit=limit)
    autoscale = compute_autoscale_recommendations(
        overview,
        target_cpu=target_cpu,
        max_cpu=max_cpu,
        min_cpu=min_cpu,
    )
    state = load_infra_state()
    backup = compute_backup_plan(state)
    result = emit_infra_missions(autoscale, backup)
    return {
        "ok": True,
        "autoscale_summary": autoscale.get("summary"),
        "backup_summary": backup.get("summary"),
        "created_missions": result.get("created_missions", 0),
        "mission_ids": result.get("mission_ids", []),
    }


@router.get("/autoscale_plan")
def infra_autoscale_plan(limit: int = 500, target_cpu: float = 0.6, max_cpu: float = 0.85, min_cpu: float = 0.15):
    """Return a conservative autoscaling-style recommendation.

    This endpoint is read-only: it inspects recent metrics and suggests
    where to add capacity or consolidate, but does not perform any
    orchestration actions.
    """

    if not _infra_enabled():
        raise HTTPException(status_code=404, detail="infra orchestrator disabled")

    overview = infra_metrics.build_infra_overview(limit=limit)
    plan = compute_autoscale_recommendations(
        overview,
        target_cpu=target_cpu,
        max_cpu=max_cpu,
        min_cpu=min_cpu,
    )
    return plan

