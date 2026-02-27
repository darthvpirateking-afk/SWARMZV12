from pathlib import Path
from typing import List

from fastapi import APIRouter
from pydantic import BaseModel, Field

from swarmz_runtime.core.fusion_registry import FusionRegistry

router = APIRouter()
_registry = FusionRegistry(Path(__file__).resolve().parent.parent.parent)


class FusionRegisterRequest(BaseModel):
    title: str
    owner: str = "operator"
    source: str = "operator_input"
    summary: str
    tags: List[str] = Field(default_factory=list)
    linked_docs: List[str] = Field(default_factory=list)


@router.post("/fusion/register")
def fusion_register(payload: FusionRegisterRequest):
    entry = _registry.register(
        title=payload.title,
        owner=payload.owner,
        source=payload.source,
        summary=payload.summary,
        tags=payload.tags,
        linked_docs=payload.linked_docs,
    )
    return {"ok": True, "entry": entry}


@router.get("/fusion/registry")
def fusion_registry():
    rows = _registry.list_entries()
    return {"ok": True, "entries": rows, "count": len(rows)}


@router.get("/fusion/verify")
def fusion_verify():
    return _registry.verify_chain()


@router.get("/fusion/summary")
def fusion_summary():
    return _registry.summary()
