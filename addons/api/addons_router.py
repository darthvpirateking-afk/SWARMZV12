# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
Addon API router â€” Bucket A features.

Endpoints for backup, replay, quarantine, budget, causal ledger,
strategy registry, drift, entropy, operator contracts, approval queue,
pack artifacts, memory boundaries, golden runs.
"""

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel
from typing import Any, Dict, List, Optional

router = APIRouter()


# â”€â”€ Request models â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

class LeverRequest(BaseModel):
    mission_id: str
    lever: str
    diff_summary: str

class StrategyRegisterRequest(BaseModel):
    strategy_id: str
    scope: str
    deps: List[str] = []
    kill_criteria: Dict[str, Any] = {}

class StrategyKillRequest(BaseModel):
    strategy_id: str
    reason: str

class StrategySealRequest(BaseModel):
    strategy_id: str
    operator_key: str

class StrategyCheckRequest(BaseModel):
    strategy_id: str
    metrics: Dict[str, float]

class BudgetSpendRequest(BaseModel):
    amount: float
    label: str

class BudgetSimRequest(BaseModel):
    cost: float

class EntropySpendRequest(BaseModel):
    points: int
    label: str

class ContractSealRequest(BaseModel):
    operator_key: str

class PatchSubmitRequest(BaseModel):
    description: str
    payload: Dict[str, Any] = {}

class PatchActionRequest(BaseModel):
    patch_id: str
    operator_key: str = ""

class PackStoreRequest(BaseModel):
    mission_id: str
    artifacts: Dict[str, str]

class MemoryPutRequest(BaseModel):
    store: str
    key: str
    value: Any

class MemoryGetRequest(BaseModel):
    store: str
    key: str

class GoldenRecordRequest(BaseModel):
    run_id: str
    inputs: Dict[str, Any]
    state_before: Any
    outputs: Dict[str, Any]
    state_after: Any

class GoldenReplayRequest(BaseModel):
    run_id: str
    replay_outputs: Dict[str, Any]
    replay_state_after: Any

class QuarantineEnterRequest(BaseModel):
    reason: str

class QuarantineExitRequest(BaseModel):
    operator_key: str


# â”€â”€ Backup â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@router.get("/backup/export")
def backup_export():
    from addons.backup import export_backup
    data = export_backup()
    return Response(content=data, media_type="application/zip",
                    headers={"Content-Disposition": "attachment; filename=swarmz_backup.zip"})


@router.post("/backup/import")
async def backup_import(request: Request):
    from addons.backup import import_backup
    body = await request.body()
    result = import_backup(body)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/backup/rollback")
def backup_rollback(rollback_path: str):
    from addons.backup import rollback_import
    result = rollback_import(rollback_path)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


# â”€â”€ Replay â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@router.get("/replay")
def replay():
    from addons.replay import replay_state
    return replay_state()


# â”€â”€ Quarantine â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@router.get("/quarantine")
def quarantine_status():
    from addons.quarantine import get_quarantine_status
    return get_quarantine_status()


@router.post("/quarantine/enter")
def quarantine_enter(req: QuarantineEnterRequest):
    from addons.quarantine import enter_quarantine
    return enter_quarantine(req.reason)


@router.post("/quarantine/exit")
def quarantine_exit(req: QuarantineExitRequest):
    from addons.quarantine import exit_quarantine
    result = exit_quarantine(req.operator_key)
    if "error" in result:
        raise HTTPException(status_code=403, detail=result["error"])
    return result


# â”€â”€ Budget â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@router.get("/budget")
def budget_get():
    from addons.budget import get_budget
    return get_budget()


@router.post("/budget/simulate")
def budget_simulate(req: BudgetSimRequest):
    from addons.budget import simulate_burn
    return simulate_burn(req.cost)


@router.post("/budget/spend")
def budget_spend(req: BudgetSpendRequest):
    from addons.budget import spend
    result = spend(req.amount, req.label)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/budget/reset")
def budget_reset():
    from addons.budget import reset_budget
    return reset_budget()


# â”€â”€ Causal Ledger â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@router.post("/ledger/declare")
def ledger_declare(req: LeverRequest):
    from addons.causal_ledger import declare_lever
    return declare_lever(req.mission_id, req.lever, req.diff_summary)


@router.get("/ledger/validate/{mission_id}")
def ledger_validate(mission_id: str):
    from addons.causal_ledger import validate_lever
    return validate_lever(mission_id)


@router.get("/ledger")
def ledger_list():
    from addons.causal_ledger import load_ledger
    return {"entries": load_ledger()}


# â”€â”€ Strategy Registry â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@router.post("/strategies/register")
def strategy_register(req: StrategyRegisterRequest):
    from addons.strategy_registry import register_strategy
    return register_strategy(req.strategy_id, req.scope, req.deps, req.kill_criteria)


@router.post("/strategies/kill")
def strategy_kill(req: StrategyKillRequest):
    from addons.strategy_registry import kill_strategy
    result = kill_strategy(req.strategy_id, req.reason)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.post("/strategies/seal")
def strategy_seal(req: StrategySealRequest):
    from addons.strategy_registry import seal_strategy
    result = seal_strategy(req.strategy_id, req.operator_key)
    if "error" in result:
        raise HTTPException(status_code=403, detail=result["error"])
    return result


@router.post("/strategies/check")
def strategy_check(req: StrategyCheckRequest):
    from addons.strategy_registry import check_kill_criteria
    return check_kill_criteria(req.strategy_id, req.metrics)


@router.get("/strategies")
def strategy_list():
    from addons.strategy_registry import list_strategies
    return {"strategies": list_strategies()}


# â”€â”€ Drift Scanner â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@router.get("/drift")
def drift_scan():
    from addons.drift_scanner import scan_all_metrics
    return {"metrics": scan_all_metrics()}


@router.post("/drift/record")
def drift_record(name: str, value: float):
    from addons.drift_scanner import record_metric
    return record_metric(name, value)


@router.get("/drift/{name}")
def drift_get(name: str):
    from addons.drift_scanner import compute_drift
    return compute_drift(name)


# â”€â”€ Entropy Budget â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@router.get("/entropy")
def entropy_get():
    from addons.entropy_budget import get_entropy_budget
    return get_entropy_budget()


@router.post("/entropy/spend")
def entropy_spend(req: EntropySpendRequest):
    from addons.entropy_budget import spend_entropy
    result = spend_entropy(req.points, req.label)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


# â”€â”€ Operator Contracts â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@router.get("/contract")
def contract_get():
    from addons.operator_contract import get_active_contract
    return get_active_contract()


@router.post("/contract")
def contract_save(contract: Dict[str, Any]):
    from addons.operator_contract import save_contract
    return save_contract(contract)


@router.post("/contract/seal")
def contract_seal(req: ContractSealRequest):
    from addons.operator_contract import seal_contract
    result = seal_contract(req.operator_key)
    if "error" in result:
        raise HTTPException(status_code=403, detail=result["error"])
    return result


@router.get("/contract/validate/{action}")
def contract_validate(action: str):
    from addons.operator_contract import validate_action
    return validate_action(action)


# â”€â”€ Approval Queue â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@router.post("/patches/submit")
def patch_submit(req: PatchSubmitRequest):
    from addons.approval_queue import submit_patch
    return submit_patch(req.description, req.payload)


@router.get("/patches")
def patch_list(status: Optional[str] = None):
    from addons.approval_queue import list_patches
    return {"patches": list_patches(status)}


@router.post("/patches/approve")
def patch_approve(req: PatchActionRequest):
    from addons.approval_queue import approve_patch
    result = approve_patch(req.patch_id, req.operator_key)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/patches/apply")
def patch_apply(req: PatchActionRequest):
    from addons.approval_queue import apply_patch
    result = apply_patch(req.patch_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/patches/rollback")
def patch_rollback(req: PatchActionRequest):
    from addons.approval_queue import rollback_patch
    result = rollback_patch(req.patch_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


# â”€â”€ Pack Artifacts â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@router.post("/packs/store")
def pack_store(req: PackStoreRequest):
    from addons.pack_artifacts import store_pack
    return store_pack(req.mission_id, req.artifacts)


@router.get("/packs")
def pack_list():
    from addons.pack_artifacts import list_packs
    return {"packs": list_packs()}


@router.get("/packs/{mission_id}/download")
def pack_download(mission_id: str):
    from addons.pack_artifacts import download_pack
    data = download_pack(mission_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Pack not found")
    return Response(content=data, media_type="application/zip",
                    headers={"Content-Disposition": f"attachment; filename={mission_id}.zip"})


@router.get("/packs/{mission_id}/verify")
def pack_verify(mission_id: str):
    from addons.pack_artifacts import verify_pack
    return verify_pack(mission_id)


# â”€â”€ Memory Boundaries â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@router.post("/memory/put")
def memory_put(req: MemoryPutRequest):
    from addons.memory_boundaries import put
    return put(req.store, req.key, req.value)


@router.get("/memory/{store}/{key}")
def memory_get(store: str, key: str):
    from addons.memory_boundaries import get
    val = get(store, key)
    if val is None:
        raise HTTPException(status_code=404, detail="Key not found")
    return {"store": store, "key": key, "value": val}


@router.get("/memory/{store}")
def memory_list(store: str):
    from addons.memory_boundaries import list_keys, dump_store
    return {"store": store, "keys": list_keys(store), "data": dump_store(store)}


# â”€â”€ Golden Run â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@router.post("/golden/record")
def golden_record(req: GoldenRecordRequest):
    from addons.golden_run import record_golden_run
    return record_golden_run(req.run_id, req.inputs, req.state_before, req.outputs, req.state_after)


@router.post("/golden/replay")
def golden_replay(req: GoldenReplayRequest):
    from addons.golden_run import replay_and_verify
    return replay_and_verify(req.run_id, req.replay_outputs, req.replay_state_after)


@router.get("/golden")
def golden_list():
    from addons.golden_run import list_golden_runs
    return {"runs": list_golden_runs()}

