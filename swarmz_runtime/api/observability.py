from fastapi import APIRouter

router = APIRouter(prefix="/v1/observability", tags=["observability"])


@router.get("/health")
def health():
    # Liveness: must be fast and side-effect free
    return {"status": "ok"}


@router.get("/ready")
def ready():
    # Readiness: keep it cheap; you can expand later if needed
    return {"status": "ready"}
