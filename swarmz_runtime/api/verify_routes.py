# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
from fastapi import APIRouter, HTTPException, Request

from swarmz_runtime.verify import runner, patchpacks, scheduler

router = APIRouter()


def _require_operator(request: Request):
    header_key = request.headers.get("X-Operator-Key")
    if not header_key:
        raise HTTPException(status_code=401, detail="operator key required")


@router.get("/v1/verify/status")
def verify_status():
    scheduler.tick()
    return runner.run_status()


@router.post("/v1/verify/run")
def verify_run():
    return runner.run_verify()


@router.post("/v1/verify/replay")
def verify_replay():
    return runner.replay_audit()


@router.post("/v1/patchpacks/generate")
def patchpack_generate(note: str = "auto"):
    return patchpacks.generate_patchpack(note)


@router.post("/v1/patchpacks/apply")
def patchpack_apply(pack_id: str, request: Request):
    _require_operator(request)
    return patchpacks.apply_patchpack(pack_id)


@router.post("/v1/patchpacks/rollback")
def patchpack_rollback(pack_id: str, request: Request):
    _require_operator(request)
    return patchpacks.rollback_patchpack(pack_id)

