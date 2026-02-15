from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from swarmz_runtime.core.engine import SwarmzEngine
from swarmz_runtime.api import missions, system, admin
from addons.api.addons_router import router as addons_router
from addons.api.guardrails_router import router as guardrails_router
from addons.api.dashboard_router import router as dashboard_router
from addons.auth_gate import LANAuthMiddleware
from addons.rate_limiter import RateLimitMiddleware

app = FastAPI(
    title="SWARMZ Runtime",
    description="Operator-Sovereign Mission Engine",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(LANAuthMiddleware)
app.add_middleware(RateLimitMiddleware)

_engine_instance = None

def get_engine() -> SwarmzEngine:
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = SwarmzEngine()
    return _engine_instance

missions.get_engine = get_engine
system.get_engine = get_engine
admin.get_engine = get_engine

app.include_router(missions.router, prefix="/v1/missions", tags=["missions"])
app.include_router(system.router, prefix="/v1/system", tags=["system"])
app.include_router(admin.router, prefix="/v1/admin", tags=["admin"])
app.include_router(addons_router, prefix="/v1/addons", tags=["addons"])
app.include_router(guardrails_router, prefix="/v1/guardrails", tags=["guardrails"])
app.include_router(dashboard_router, tags=["dashboard"])

@app.get("/")
def root():
    return {
        "name": "SWARMZ Runtime",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs",
        "dashboard": "/dashboard"
    }


@app.on_event("startup")
def on_startup():
    from addons.schema_version import run_migrations
    run_migrations()

@app.get("/health")
def health_check():
    return get_engine().get_health()
