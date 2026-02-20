from fastapi import APIRouter, Query, Request
from typing import Optional
from datetime import datetime, timezone

v1_stubs_router = APIRouter(
    tags=["v1"]
)


@v1_stubs_router.get("/prepared/pending")
async def get_prepared_pending(tag: Optional[str] = Query(default=None)):
    # Example stub: match test contract exactly
    items = []
    if tag:
        items = [p for p in items if p.get("tag") == tag]
    counts = {"total": len(items)}
    return {
        "ok": True,
        "items": items,
        "counts": counts
    }


@v1_stubs_router.get("/ai/status")
async def get_ai_status(request: Request):
    orch = getattr(request.app.state, "orchestrator", None)
    phase = getattr(orch, "phase", None) if orch is not None else None
    return {
        "ok": True,
        "phase": phase or "quarantine",
        "quarantine": True,
        "ts": datetime.now(timezone.utc).isoformat(),
    }
