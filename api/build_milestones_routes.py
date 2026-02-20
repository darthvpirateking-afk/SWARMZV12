from fastapi import APIRouter

from api.build_milestones_models import (
    BuildMilestonesPromoteRequest,
    BuildMilestonesPromoteResponse,
    BuildMilestonesStatusResponse,
)
from api.build_milestones_service import BuildMilestonesService

router = APIRouter(prefix="/v1/build/milestones", tags=["build-milestones"])
_service = BuildMilestonesService(data_dir="data")


@router.get("/status", response_model=BuildMilestonesStatusResponse)
async def build_milestones_status() -> BuildMilestonesStatusResponse:
    return _service.get_status()


@router.post("/promote", response_model=BuildMilestonesPromoteResponse)
async def build_milestones_promote(
    payload: BuildMilestonesPromoteRequest,
) -> BuildMilestonesPromoteResponse:
    return _service.promote(payload.target_stage)
