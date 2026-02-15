from fastapi import APIRouter
from swarmz_runtime.core.engine import SwarmzEngine

router = APIRouter()
engine = SwarmzEngine()


@router.get("/health")
def get_health():
    return engine.get_health()


@router.get("/omens")
def get_omens():
    omens = engine.get_omens()
    return {"omens": omens, "count": len(omens)}


@router.get("/predictions")
def get_predictions():
    prophecies = engine.get_predictions()
    return {"prophecies": prophecies, "count": len(prophecies)}


@router.get("/templates")
def get_templates():
    runes = engine.get_runes()
    return {"templates": runes, "count": len(runes)}
