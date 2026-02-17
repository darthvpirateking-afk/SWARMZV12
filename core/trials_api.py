# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
SWARMZ Trials API â€” FastAPI endpoints for the Trials Inbox system.

Add-only module. Import and call register_trials_api(app) from server.py
to mount all trial endpoints under /v1/trials/*.
"""

from typing import Optional, List
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException


# â”€â”€ Request/Response Models â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

class CreateTrialRequest(BaseModel):
    action: str
    context: str
    metric_name: str
    check_after_sec: int = 300
    expected_delta: Optional[float] = None
    created_by: str = "operator"
    tags: Optional[List[str]] = None
    notes: Optional[str] = None


class NonTrialRequest(BaseModel):
    action: str
    context: str
    reason: str
    created_by: str = "admin"


class AddNoteRequest(BaseModel):
    note: str


class FollowupRequest(BaseModel):
    action: Optional[str] = None
    context: Optional[str] = None
    metric_name: Optional[str] = None
    check_after_sec: Optional[int] = None
    expected_delta: Optional[float] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = None
    created_by: str = "operator"


def register_trials_api(app: FastAPI) -> None:
    """Mount all /v1/trials/* endpoints on the given FastAPI app."""

    # â”€â”€ POST /v1/trials/create â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    @app.post("/v1/trials/create")
    async def create_trial(payload: CreateTrialRequest):
        try:
            from core.trials import new_trial
            trial = new_trial(
                created_by=payload.created_by,
                context=payload.context,
                action=payload.action,
                metric_name=payload.metric_name,
                check_after_sec=payload.check_after_sec,
                expected_delta=payload.expected_delta,
                tags=payload.tags,
                notes=payload.notes,
            )
            return {"ok": True, "trial": trial}
        except Exception as e:
            return {"ok": False, "error": str(e)[:300]}

    # â”€â”€ POST /v1/trials/gate â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    @app.post("/v1/trials/gate")
    async def trial_gate(payload: CreateTrialRequest):
        """Gate endpoint: forces a Trial for a meaningful change."""
        try:
            from core.trials import require_trial
            trial = require_trial(
                action=payload.action,
                context=payload.context,
                metric_name=payload.metric_name,
                check_after_sec=payload.check_after_sec,
                created_by=payload.created_by,
                expected_delta=payload.expected_delta,
                tags=payload.tags,
                notes=payload.notes,
            )
            return {"ok": True, "trial": trial}
        except Exception as e:
            return {"ok": False, "error": str(e)[:300]}

    # â”€â”€ POST /v1/trials/exempt â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    @app.post("/v1/trials/exempt")
    async def trial_exempt(payload: NonTrialRequest):
        """Mark a change as non-trial (admin-only, with reason)."""
        try:
            from core.trials import require_trial
            result = require_trial(
                action=payload.action,
                context=payload.context,
                metric_name="conversion_rate",
                non_trial_reason=payload.reason,
                created_by=payload.created_by,
                admin=True,
            )
            return {"ok": True, "exempted": True, "reason": payload.reason}
        except Exception as e:
            return {"ok": False, "error": str(e)[:300]}

    # â”€â”€ GET /v1/trials/inbox â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    @app.get("/v1/trials/inbox")
    async def trials_inbox(tab: str = "pending", limit: int = 50):
        """
        Retrieve inbox items.
        tab: pending | needs_review | completed | all
        """
        try:
            from core.trials import inbox_pending, inbox_needs_review, inbox_completed, inbox_counts
            counts = inbox_counts()

            if tab == "pending":
                items = inbox_pending()
            elif tab == "needs_review":
                items = inbox_needs_review()
            elif tab == "completed":
                items = inbox_completed()
            elif tab == "all":
                items = inbox_pending() + inbox_needs_review() + inbox_completed()
            else:
                items = inbox_pending()

            return {
                "ok": True,
                "tab": tab,
                "items": items[:limit],
                "counts": counts,
            }
        except Exception as e:
            return {"ok": False, "error": str(e)[:300], "items": [], "counts": {}}

    # â”€â”€ GET /v1/trials/counts â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    @app.get("/v1/trials/counts")
    async def trials_counts():
        try:
            from core.trials import inbox_counts
            return {"ok": True, **inbox_counts()}
        except Exception as e:
            return {"ok": False, "error": str(e)[:300]}

    # â”€â”€ GET /v1/trials/{trial_id} â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    @app.get("/v1/trials/detail/{trial_id}")
    async def trial_detail(trial_id: str):
        try:
            from core.trials import get_trial, get_audit_trail
            trial = get_trial(trial_id)
            if not trial:
                raise HTTPException(status_code=404, detail="Trial not found")
            audit = get_audit_trail(trial_id=trial_id, tail=30)
            return {"ok": True, "trial": trial, "audit": audit}
        except HTTPException:
            raise
        except Exception as e:
            return {"ok": False, "error": str(e)[:300]}

    # â”€â”€ POST /v1/trials/{trial_id}/revert â”€â”€â”€â”€â”€â”€â”€â”€â”€

    @app.post("/v1/trials/{trial_id}/revert")
    async def trial_revert(trial_id: str):
        try:
            from core.trials import revert_trial
            result = revert_trial(trial_id)
            if not result:
                raise HTTPException(status_code=404, detail="Trial not found")
            return {"ok": True, **result}
        except HTTPException:
            raise
        except Exception as e:
            return {"ok": False, "error": str(e)[:300]}

    # â”€â”€ POST /v1/trials/{trial_id}/note â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    @app.post("/v1/trials/{trial_id}/note")
    async def trial_note(trial_id: str, payload: AddNoteRequest):
        try:
            from core.trials import add_note
            result = add_note(trial_id, payload.note)
            if not result:
                raise HTTPException(status_code=404, detail="Trial not found")
            return {"ok": True, "trial": result}
        except HTTPException:
            raise
        except Exception as e:
            return {"ok": False, "error": str(e)[:300]}

    # â”€â”€ POST /v1/trials/{trial_id}/followup â”€â”€â”€â”€â”€â”€â”€

    @app.post("/v1/trials/{trial_id}/followup")
    async def trial_followup(trial_id: str, payload: FollowupRequest):
        try:
            from core.trials import create_followup
            overrides = {}
            if payload.action:
                overrides["action"] = payload.action
            if payload.context:
                overrides["context"] = payload.context
            if payload.metric_name:
                overrides["metric_name"] = payload.metric_name
            if payload.check_after_sec:
                overrides["check_after_sec"] = payload.check_after_sec
            if payload.expected_delta is not None:
                overrides["expected_delta"] = payload.expected_delta
            if payload.tags:
                overrides["tags"] = payload.tags
            if payload.notes:
                overrides["notes"] = payload.notes

            result = create_followup(trial_id, created_by=payload.created_by, **overrides)
            if not result:
                raise HTTPException(status_code=404, detail="Trial not found")
            return {"ok": True, "trial": result}
        except HTTPException:
            raise
        except Exception as e:
            return {"ok": False, "error": str(e)[:300]}

    # â”€â”€ GET /v1/trials/metrics â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    @app.get("/v1/trials/metrics")
    async def trials_metrics():
        """List available metrics and resolve each one."""
        try:
            from core.trials import list_available_metrics, resolve_metric
            metrics = list_available_metrics()
            resolved = {}
            for m in metrics:
                try:
                    val, ev = resolve_metric(m, "global")
                    resolved[m] = {"value": val, "evidence": ev}
                except Exception:
                    resolved[m] = {"value": None, "evidence": {"error": "resolve failed"}}
            return {"ok": True, "metrics": metrics, "resolved": resolved}
        except Exception as e:
            return {"ok": False, "error": str(e)[:300]}

    # â”€â”€ GET /v1/trials/scores â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    @app.get("/v1/trials/scores")
    async def trials_scores(limit: int = 20):
        """Return survival leaderboard."""
        try:
            from core.trials import get_survival_leaderboard
            items = get_survival_leaderboard(limit=limit)
            return {"ok": True, "scores": items}
        except Exception as e:
            return {"ok": False, "error": str(e)[:300], "scores": []}

    # â”€â”€ GET /v1/trials/audit â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    @app.get("/v1/trials/audit")
    async def trials_audit(trial_id: Optional[str] = None, tail: int = 50):
        try:
            from core.trials import get_audit_trail
            events = get_audit_trail(trial_id=trial_id, tail=tail)
            return {"ok": True, "events": events}
        except Exception as e:
            return {"ok": False, "error": str(e)[:300], "events": []}

    # â”€â”€ GET /v1/trials/worker/status â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    @app.get("/v1/trials/worker/status")
    async def trials_worker_status():
        try:
            from core.trials_worker import worker_status
            return {"ok": True, **worker_status()}
        except Exception as e:
            return {"ok": False, "error": str(e)[:300]}

    # â”€â”€ POST /v1/trials/worker/start â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    @app.post("/v1/trials/worker/start")
    async def trials_worker_start():
        try:
            from core.trials_worker import start_worker
            started = start_worker()
            return {"ok": True, "started": started}
        except Exception as e:
            return {"ok": False, "error": str(e)[:300]}

    # â”€â”€ POST /v1/trials/worker/check-now â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

    @app.post("/v1/trials/worker/check-now")
    async def trials_worker_check_now():
        """Manually trigger a check cycle."""
        try:
            from core.trials_worker import check_due_trials
            count = check_due_trials()
            return {"ok": True, "evaluated": count}
        except Exception as e:
            return {"ok": False, "error": str(e)[:300]}

