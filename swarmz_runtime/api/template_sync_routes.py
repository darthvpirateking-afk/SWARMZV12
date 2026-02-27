from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from swarmz_runtime.core.template_sync import TemplateSyncManager

router = APIRouter()
_manager = TemplateSyncManager(Path(__file__).resolve().parent.parent.parent)


class TemplateSyncConfigRequest(BaseModel):
    operator_id: str
    allowlist: Optional[List[str]] = None
    auto_sync: Optional[bool] = None
    sync_interval_hours: Optional[int] = None


class QueueTemplateSyncRequest(BaseModel):
    operator_id: str
    source_url: str
    template_name: str
    dry_run: bool = True
    notes: str = ""


class CompanionBondRequest(BaseModel):
    operator_id: str
    tone: str = "loyal"
    style: str = "direct"
    focus: str = "operator_success"


_bond_state: Dict[str, Any] = {
    "operator_id": "",
    "tone": "loyal",
    "style": "direct",
    "focus": "operator_success",
}


@router.get("/template-sync/config")
def get_template_sync_config():
    return {"ok": True, "config": _manager.get_config()}


@router.post("/template-sync/config")
def update_template_sync_config(payload: TemplateSyncConfigRequest):
    cfg = _manager.update_config(
        operator_id=payload.operator_id,
        allowlist=payload.allowlist,
        auto_sync=payload.auto_sync,
        sync_interval_hours=payload.sync_interval_hours,
    )
    return {"ok": True, "config": cfg}


@router.post("/template-sync/queue")
def queue_template_sync(payload: QueueTemplateSyncRequest):
    result = _manager.queue_sync(
        operator_id=payload.operator_id,
        source_url=payload.source_url,
        template_name=payload.template_name,
        dry_run=payload.dry_run,
        notes=payload.notes,
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/template-sync/jobs")
def list_template_sync_jobs(limit: int = 50):
    jobs = _manager.list_jobs(limit)
    return {"ok": True, "jobs": jobs, "count": len(jobs)}


@router.get("/template-sync/templates")
def list_template_sync_templates(limit: int = 50):
    templates = _manager.list_templates(limit)
    return {"ok": True, "templates": templates, "count": len(templates)}


@router.post("/companion/bond")
def set_companion_bond(payload: CompanionBondRequest):
    _bond_state["operator_id"] = payload.operator_id
    _bond_state["tone"] = payload.tone
    _bond_state["style"] = payload.style
    _bond_state["focus"] = payload.focus
    return {
        "ok": True,
        "bond": _bond_state,
        "note": "Personalization enabled for this operator profile. This is preference alignment, not sentience.",
    }


@router.get("/companion/bond")
def get_companion_bond():
    return {"ok": True, "bond": _bond_state}
