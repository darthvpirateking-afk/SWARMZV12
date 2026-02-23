from fastapi import APIRouter

from api.operator_auth_models import (
    OperatorAuthStatusResponse,
    OperatorAuthVerifyRequest,
    OperatorAuthVerifyResponse,
)
from api.operator_auth_service import OperatorAuthService

router = APIRouter(prefix="/v1/operator/auth", tags=["operator-auth"])
_service = OperatorAuthService(data_dir="data")


@router.get("/status", response_model=OperatorAuthStatusResponse)
async def operator_auth_status() -> OperatorAuthStatusResponse:
    return _service.get_status()


@router.post("/verify", response_model=OperatorAuthVerifyResponse)
async def operator_auth_verify(
    payload: OperatorAuthVerifyRequest,
) -> OperatorAuthVerifyResponse:
    return _service.verify(payload.operator_key)
