# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
SWARMZ Hologram Evolution Ladder â€” FastAPI endpoints.

Add-only module.  Import and call register_hologram_api(app) from server.py
to mount all hologram endpoints under /v1/hologram/*.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException

# â”€â”€ Request models â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€


class BurstToggleRequest(BaseModel):
    enabled: bool


class BurstBatchTrialSpec(BaseModel):
    action: str
    context: str = "burst"
    metric_name: str = "conversion_rate"
    check_after_sec: int = 300
    expected_delta: Optional[float] = None
    tags: Optional[List[str]] = None


class BurstBatchRequest(BaseModel):
    trials: List[BurstBatchTrialSpec]
    budget_sec: int = 3600
    max_parallel: int = 10
    created_by: str = "burst"


class DriftCheckRequest(BaseModel):
    metric_name: str
    context: str
    window_days: int = 7


class SuggestionRequest(BaseModel):
    context: str
    limit: int = 5


def register_hologram_api(app: FastAPI) -> None:
    """Mount all /v1/hologram/* endpoints on the given FastAPI app."""

    # â”€â”€ GET /v1/hologram/state â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    @app.get("/v1/hologram/state")
    async def hologram_state():
        """Full evolution state: level, XP, currencies, powers."""
        try:
            from core.hologram import compute_level

            state = compute_level()
            return {"ok": True, **state}
        except Exception as exc:
            return {"ok": False, "error": str(exc)[:300]}

    # â”€â”€ GET /v1/hologram/xp â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    @app.get("/v1/hologram/xp")
    async def hologram_xp():
        """Quick XP check."""
        try:
            from core.hologram import compute_xp, compute_level

            xp = compute_xp()
            level_data = compute_level()
            return {
                "ok": True,
                "xp": xp,
                "level": level_data["level"],
                "name": level_data["name"],
            }
        except Exception as exc:
            return {"ok": False, "error": str(exc)[:300]}

    # â”€â”€ GET /v1/hologram/currencies â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    @app.get("/v1/hologram/currencies")
    async def hologram_currencies():
        """Power currencies: stability, novelty, reversibility."""
        try:
            from core.hologram import compute_power_currencies

            currencies = compute_power_currencies()
            return {"ok": True, **currencies}
        except Exception as exc:
            return {"ok": False, "error": str(exc)[:300]}

    # â”€â”€ GET /v1/hologram/powers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    @app.get("/v1/hologram/powers")
    async def hologram_powers():
        """Currently unlocked powers."""
        try:
            from core.hologram import compute_level

            state = compute_level()
            return {
                "ok": True,
                "level": state["level"],
                "name": state["name"],
                "powers": state["powers"],
            }
        except Exception as exc:
            return {"ok": False, "error": str(exc)[:300]}

    # â”€â”€ GET /v1/hologram/levels â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    @app.get("/v1/hologram/levels")
    async def hologram_levels():
        """All level definitions."""
        try:
            from core.hologram import LEVELS

            return {"ok": True, "levels": LEVELS}
        except Exception as exc:
            return {"ok": False, "error": str(exc)[:300]}

    # â”€â”€ GET /v1/hologram/trial/{trial_id} â”€â”€â”€â”€â”€â”€â”€â”€â”€

    @app.get("/v1/hologram/trial/{trial_id}")
    async def hologram_trial(trial_id: str):
        """Level-gated trial detail for the hologram panel."""
        try:
            from core.hologram import hologram_trial_detail

            detail = hologram_trial_detail(trial_id)
            if not detail.get("ok"):
                raise HTTPException(
                    status_code=404, detail=detail.get("error", "Not found")
                )
            return detail
        except HTTPException:
            raise
        except Exception as exc:
            return {"ok": False, "error": str(exc)[:300]}

    # â”€â”€ GET /v1/hologram/effects/{trial_id} â”€â”€â”€â”€â”€â”€â”€

    @app.get("/v1/hologram/effects/{trial_id}")
    async def hologram_effects(trial_id: str):
        """Compute visual effects for a specific trial."""
        try:
            from core.hologram import compute_effects, compute_level
            from core.trials import get_trial

            trial = get_trial(trial_id)
            if not trial:
                raise HTTPException(status_code=404, detail="Trial not found")
            level_data = compute_level()
            effects = compute_effects(trial, level_data["level"])
            return {"ok": True, **effects}
        except HTTPException:
            raise
        except Exception as exc:
            return {"ok": False, "error": str(exc)[:300]}

    # â”€â”€ POST /v1/hologram/drift/check â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    @app.post("/v1/hologram/drift/check")
    async def hologram_drift_check(payload: DriftCheckRequest):
        """Check for metric drift (LV4+ power)."""
        try:
            from core.hologram import detect_drift, compute_level

            level_data = compute_level()
            if level_data["level"] < 4:
                return {
                    "ok": False,
                    "error": f"Drift detection requires LV4 (MEGA). Current: LV{level_data['level']}",
                }
            result = detect_drift(
                metric_name=payload.metric_name,
                context=payload.context,
                window_days=payload.window_days,
            )
            return {"ok": True, **result}
        except Exception as exc:
            return {"ok": False, "error": str(exc)[:300]}

    # â”€â”€ POST /v1/hologram/drift/suggest â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    @app.post("/v1/hologram/drift/suggest")
    async def hologram_drift_suggest(payload: DriftCheckRequest):
        """Suggest drift correction trial (LV4+ power, never auto-exec)."""
        try:
            from core.hologram import suggest_drift_correction, compute_level

            level_data = compute_level()
            if level_data["level"] < 4:
                return {
                    "ok": False,
                    "error": f"Drift suggestions require LV4 (MEGA). Current: LV{level_data['level']}",
                }
            suggestion = suggest_drift_correction(
                metric_name=payload.metric_name,
                context=payload.context,
            )
            if suggestion is None:
                return {"ok": True, "suggestion": None, "reason": "No drift detected"}
            return {"ok": True, "suggestion": suggestion}
        except Exception as exc:
            return {"ok": False, "error": str(exc)[:300]}

    # â”€â”€ POST /v1/hologram/burst/toggle â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    @app.post("/v1/hologram/burst/toggle")
    async def hologram_burst_toggle(payload: BurstToggleRequest):
        """Toggle Burst Mode on/off."""
        try:
            from core.hologram import toggle_burst_mode

            result = toggle_burst_mode(payload.enabled)
            return result
        except Exception as exc:
            return {"ok": False, "error": str(exc)[:300]}

    # â”€â”€ POST /v1/hologram/burst/batch â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    @app.post("/v1/hologram/burst/batch")
    async def hologram_burst_batch(payload: BurstBatchRequest):
        """Create a burst batch of parallel trials."""
        try:
            from core.hologram import create_burst_batch

            specs = [t.model_dump() for t in payload.trials]
            result = create_burst_batch(
                trials_specs=specs,
                budget_sec=payload.budget_sec,
                max_parallel=payload.max_parallel,
                created_by=payload.created_by,
            )
            return result
        except Exception as exc:
            return {"ok": False, "error": str(exc)[:300]}

    # â”€â”€ POST /v1/hologram/burst/kill/{batch_id} â”€â”€

    @app.post("/v1/hologram/burst/kill/{batch_id}")
    async def hologram_burst_kill(batch_id: str):
        """Kill switch: revert all trials in a burst batch."""
        try:
            from core.hologram import kill_burst_batch

            result = kill_burst_batch(batch_id)
            return result
        except Exception as exc:
            return {"ok": False, "error": str(exc)[:300]}

    # â”€â”€ GET /v1/hologram/burst/batches â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    @app.get("/v1/hologram/burst/batches")
    async def hologram_burst_batches():
        """List recent burst batches."""
        try:
            from core.hologram import list_burst_batches

            batches = list_burst_batches()
            return {"ok": True, "batches": batches}
        except Exception as exc:
            return {"ok": False, "error": str(exc)[:300]}

    # â”€â”€ POST /v1/hologram/suggest/followups â”€â”€â”€â”€â”€â”€

    @app.post("/v1/hologram/suggest/followups")
    async def hologram_suggest_followups(payload: SuggestionRequest):
        """Suggest best follow-up trials based on survival scores (LV3+)."""
        try:
            from core.hologram import suggest_best_followups, compute_level

            level_data = compute_level()
            if level_data["level"] < 3:
                return {
                    "ok": False,
                    "error": f"Follow-up suggestions require LV3 (ULTIMATE). Current: LV{level_data['level']}",
                }
            suggestions = suggest_best_followups(
                context=payload.context,
                limit=payload.limit,
            )
            return {"ok": True, "suggestions": suggestions}
        except Exception as exc:
            return {"ok": False, "error": str(exc)[:300]}
