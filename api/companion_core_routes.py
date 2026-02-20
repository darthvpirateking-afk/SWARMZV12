from fastapi import APIRouter

from api.companion_core_models import (
    CompanionCoreMessageRequest,
    CompanionCoreMessageResponse,
    CompanionCoreStatusResponse,
)
from api.companion_core_service import CompanionCoreService

router = APIRouter(prefix="/v1/companion/core", tags=["companion-core"])
_service = CompanionCoreService()


@router.get("/status", response_model=CompanionCoreStatusResponse)
async def companion_core_status() -> CompanionCoreStatusResponse:
    return _service.get_status()


@router.post("/message", response_model=CompanionCoreMessageResponse)
async def companion_core_message(payload: CompanionCoreMessageRequest) -> CompanionCoreMessageResponse:
    return _service.message(payload.text)
