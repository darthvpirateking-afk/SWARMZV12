# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
from fastapi import APIRouter
from typing import Callable
from swarmz_runtime.core.engine import SwarmzEngine

router = APIRouter()

get_engine: Callable[[], SwarmzEngine] = lambda: SwarmzEngine()


@router.get("/health")
def get_health():
    return get_engine().get_health()


@router.get("/omens")
def get_omens():
    omens = get_engine().get_omens()
    return {"omens": omens, "count": len(omens)}


@router.get("/predictions")
def get_predictions():
    prophecies = get_engine().get_predictions()
    return {"prophecies": prophecies, "count": len(prophecies)}


@router.get("/templates")
def get_templates():
    runes = get_engine().get_runes()
    return {"templates": runes, "count": len(runes)}

