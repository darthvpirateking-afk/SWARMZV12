from fastapi import APIRouter

from api.bootstrap_models import BootstrapManifestResponse, BootstrapStatusResponse
from api.bootstrap_service import BootstrapService

router = APIRouter(prefix="/v1/bootstrap", tags=["bootstrap"])
_service = BootstrapService()


@router.get("/status", response_model=BootstrapStatusResponse)
async def bootstrap_status() -> BootstrapStatusResponse:
    return _service.get_status()


@router.get("/manifest", response_model=BootstrapManifestResponse)
async def bootstrap_manifest() -> BootstrapManifestResponse:
    return _service.get_manifest()
