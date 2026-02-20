from fastapi import APIRouter

from api.database_models import (
    DatabaseCollectionsResponse,
    DatabaseStatsResponse,
    DatabaseStatusResponse,
)
from api.database_service import DatabaseService

router = APIRouter(prefix="/v1/db", tags=["database"])
_service = DatabaseService(data_dir="data")


@router.get("/status", response_model=DatabaseStatusResponse)
async def db_status() -> DatabaseStatusResponse:
    return _service.get_status()


@router.get("/collections", response_model=DatabaseCollectionsResponse)
async def db_collections() -> DatabaseCollectionsResponse:
    return _service.get_collections()


@router.get("/stats", response_model=DatabaseStatsResponse)
async def db_stats() -> DatabaseStatsResponse:
    return _service.get_stats()
