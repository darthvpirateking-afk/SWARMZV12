# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
FastAPI surface for the SWARMZ Market Lab.

Call register_market_lab_api(app) from server.py to mount:
- POST /v1/market_lab/backtest
- POST /v1/market_lab/self_check
"""

from fastapi import FastAPI, HTTPException
from core.market_lab import backtest_strategy, self_check


def register_market_lab_api(app: FastAPI) -> None:
    """Mount /v1/market_lab/* endpoints on the given FastAPI app."""

    @app.post("/v1/market_lab/backtest")
    async def market_lab_backtest(csv_path: str, strategy: dict):
        try:
            result = backtest_strategy(csv_path, strategy)
            if not result.get("ok"):
                raise HTTPException(status_code=400, detail=result.get("error"))
            return result
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    @app.post("/v1/market_lab/self_check")
    async def market_lab_self_check() -> dict:
        try:
            result = self_check()
            return result
        except Exception as exc:
            return {"ok": False, "error": str(exc)}
