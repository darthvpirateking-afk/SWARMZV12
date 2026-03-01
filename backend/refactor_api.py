from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter

from backend.refactor_scaffold import HINTS, analyze_structure

router = APIRouter()


@router.get("/v1/nexusmon/refactor/hints")
async def refactor_hints():
    if not HINTS:
        analyze_structure()
    return [asdict(h) for h in HINTS]
