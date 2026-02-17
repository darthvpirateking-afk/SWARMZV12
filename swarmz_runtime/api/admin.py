# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
from fastapi import APIRouter
from typing import Callable
from swarmz_runtime.core.engine import SwarmzEngine

router = APIRouter()

get_engine: Callable[[], SwarmzEngine] = lambda: SwarmzEngine()


@router.post("/maintenance")
def schedule_maintenance():
    result = get_engine().schedule_maintenance()
    return result

