from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

from galileo.run import run_galileo
from galileo.storage import ensure_storage
from swarmz_runtime.api.galileo_storage_shim import read_hypotheses, read_experiments, read_runs

router = APIRouter(prefix="/v1/galileo", tags=["galileo"])


class GalileoRunBody(BaseModel):
    domain: str = Field(..., min_length=1)
    seed: int = Field(..., ge=0)
    n_hypotheses: int = Field(5, ge=1, le=50)


@router.post("/run")
def galileo_run(body: GalileoRunBody) -> Dict[str, Any]:
    ensure_storage()
    result = run_galileo(domain=body.domain, seed=body.seed, n_hypotheses=body.n_hypotheses)

    # Expect run_galileo to return a dict-like result.
    return {
        "run_id": result.get("run_id"),
        "accepted_hypothesis_ids": result.get("accepted_hypothesis_ids", []),
        "experiment_ids": result.get("experiment_ids", []),
    }


@router.get("/hypotheses")
def galileo_hypotheses(domain: Optional[str] = None, status: Optional[str] = None) -> List[Dict[str, Any]]:
    ensure_storage()
    items = read_hypotheses()
    if domain:
        items = [x for x in items if x.get("domain") == domain]
    if status:
        items = [x for x in items if x.get("status") == status]
    return items


@router.get("/experiments")
def galileo_experiments(status: Optional[str] = None) -> List[Dict[str, Any]]:
    ensure_storage()
    items = read_experiments()
    if status:
        items = [x for x in items if x.get("status") == status]
    return items


@router.get("/runs/{run_id}")
def galileo_run_get(run_id: str) -> Dict[str, Any]:
    ensure_storage()
    items = read_runs()
    for r in items:
        if r.get("run_id") == run_id:
            return r
    raise HTTPException(status_code=404, detail="run_id not found")
