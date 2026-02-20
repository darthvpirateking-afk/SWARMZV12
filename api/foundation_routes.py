from fastapi import APIRouter, FastAPI

from api.foundation_models import (
    ApiFoundationDomainsResponse,
    ApiFoundationRoutesResponse,
    ApiFoundationStatusResponse,
)
from api.foundation_service import ApiFoundationService


def build_foundation_router(app: FastAPI) -> APIRouter:
    router = APIRouter(prefix="/v1/api", tags=["api-foundation"])
    service = ApiFoundationService(app)

    @router.get("/status", response_model=ApiFoundationStatusResponse)
    async def api_status() -> ApiFoundationStatusResponse:
        return service.get_status()

    @router.get("/routes", response_model=ApiFoundationRoutesResponse)
    async def api_routes() -> ApiFoundationRoutesResponse:
        return service.get_routes()

    @router.get("/domains", response_model=ApiFoundationDomainsResponse)
    async def api_domains() -> ApiFoundationDomainsResponse:
        return service.get_domains()

    return router
