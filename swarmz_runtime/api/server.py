from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from swarmz_runtime.core.engine import SwarmzEngine
from swarmz_runtime.api import missions, system, admin

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

engine = SwarmzEngine()

app.include_router(missions.router, prefix="/v1/missions", tags=["missions"])
app.include_router(system.router, prefix="/v1/system", tags=["system"])
app.include_router(admin.router, prefix="/v1/admin", tags=["admin"])

@app.get("/")
def root():
    return {
        "name": "SWARMZ Runtime",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs"
    }

@app.get("/health")
def health_check():
    return engine.get_health()
