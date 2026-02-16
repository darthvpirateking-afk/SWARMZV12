"""
arena API router – REST endpoints for ARENA v0.1.

Endpoints:
  POST /v1/arena/run      – Start an arena run
  GET  /v1/arena/runs      – List arena runs
  GET  /v1/arena/runs/{id} – Get arena run details
  GET  /v1/arena/config    – Get arena config
  GET  /v1/arena/check     – Self-check
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Any, Callable, Dict, Optional

router = APIRouter()

# Engine provider – wired by server.py
get_engine: Optional[Callable] = None


class ArenaRunRequest(BaseModel):
    prompt: str
    num_candidates: int = Field(default=3, ge=1, le=8)
    scoring_strategy: str = "length_quality"


@router.post("/run")
def start_arena_run(req: ArenaRunRequest):
    """Start a new arena run with N parallel candidates."""
    engine = get_engine()
    from swarmz_runtime.arena.engine import ArenaEngine
    from swarmz_runtime.arena.store import ArenaStore

    store = ArenaStore(str(engine.db.data_dir))
    arena = ArenaEngine(store, audit_fn=engine.db.log_audit)

    result = arena.start_run(
        prompt=req.prompt,
        num_candidates=req.num_candidates,
        scoring_strategy=req.scoring_strategy,
    )
    return result


@router.get("/runs")
def list_arena_runs(limit: int = 50):
    """List recent arena runs."""
    engine = get_engine()
    from swarmz_runtime.arena.store import ArenaStore

    store = ArenaStore(str(engine.db.data_dir))
    runs = store.list_runs(limit)
    return {"runs": runs, "count": len(runs)}


@router.get("/runs/{run_id}")
def get_arena_run(run_id: str):
    """Get details for a specific arena run."""
    engine = get_engine()
    from swarmz_runtime.arena.engine import ArenaEngine
    from swarmz_runtime.arena.store import ArenaStore

    store = ArenaStore(str(engine.db.data_dir))
    arena = ArenaEngine(store)

    run = arena.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Arena run not found")
    return run


@router.get("/config")
def get_arena_config():
    """Get current arena configuration."""
    from swarmz_runtime.arena.config import load_config
    config = load_config()
    return config.model_dump(mode="json")


@router.get("/check")
def arena_self_check():
    """Run arena self-check diagnostics."""
    from swarmz_runtime.arena.config import self_check
    ok, issues = self_check()
    return {"ok": ok, "issues": issues}
