"""Governance Router - FastAPI endpoints for the NEXUSMON governance pipeline.

Exposes live telemetry from the 12-layer governance engine:
  GET /v1/governance/status         - last known pass/fail per layer
  GET /v1/governance/perf           - P50/P95/P99 latency + block rates
  GET /v1/governance/sovereign/log  - sovereign override history
  GET /v1/governance/shadow/log     - shadow-channel decision log
  GET /v1/governance/emergence      - detected emergence patterns
  GET /v1/governance/uplift         - capability tier / maturity status
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Query

from core.governance_perf import perf_ledger

router = APIRouter(prefix="/v1/governance", tags=["governance"])

# ---------------------------------------------------------------------------
# Helper: safe module imports (non-fatal — router still loads if a module is
# missing, it just returns an "unavailable" payload for that endpoint).
# ---------------------------------------------------------------------------

try:
    from core.sovereign import get_override_history as _get_override_history

    _sovereign_available = True
except Exception:
    _sovereign_available = False


try:
    from core.shadow_channel import query_shadow_log as _query_shadow_log

    _shadow_available = True
except Exception:
    _shadow_available = False


try:
    from core.emergence import _emergence  # module-level singleton

    _emergence_available = True
except Exception:
    _emergence_available = False


try:
    from core.uplift import (
        get_locked_capabilities as _get_locked,
        get_unlocked_capabilities as _get_unlocked,
        _uplift,
    )

    _uplift_available = True
except Exception:
    _uplift_available = False


# ---------------------------------------------------------------------------
# /v1/governance/status
# ---------------------------------------------------------------------------


@router.get("/status")
async def governance_status() -> Dict[str, Any]:
    """Return last recorded pass/fail for each governance layer.

    Derived from the perf ledger — each layer's ``pass_count`` and
    ``block_count`` reflect all samples collected since server start (or last
    reset).  The ``last_result`` field reads ``pass`` when the most recent
    sample was a pass, ``block`` otherwise.
    """
    summary = perf_ledger.summary()
    layers_out: Dict[str, Any] = {}

    for name, data in summary.get("layers", {}).items():
        total = data.get("total_calls", 0)
        block_count = data.get("block_count", 0)
        pass_count = data.get("pass_count", 0)

        if total == 0:
            last_result = "unknown"
        elif pass_count >= block_count:
            last_result = "pass"
        else:
            last_result = "block"

        layers_out[name] = {
            "last_result": last_result,
            "pass_count": pass_count,
            "block_count": block_count,
            "total_calls": total,
        }

    return {
        "layers": layers_out,
        "pipeline": {
            "total_calls": summary.get("pipeline", {}).get("total_calls", 0),
            "pass_count": summary.get("pipeline", {}).get("pass_count", 0),
            "block_count": summary.get("pipeline", {}).get("block_count", 0),
        },
        "alerts": summary.get("alerts", []),
    }


# ---------------------------------------------------------------------------
# /v1/governance/perf
# ---------------------------------------------------------------------------


@router.get("/perf")
async def governance_perf() -> Dict[str, Any]:
    """Return full P50/P95/P99 latency profile for every governance layer."""
    return perf_ledger.summary()


# ---------------------------------------------------------------------------
# /v1/governance/sovereign/log
# ---------------------------------------------------------------------------


@router.get("/sovereign/log")
async def sovereign_log(limit: int = Query(default=50, ge=1, le=500)) -> Dict[str, Any]:
    """Return the last *limit* sovereign override events."""
    if not _sovereign_available:
        return {
            "available": False,
            "entries": [],
            "message": "sovereign module not loaded",
        }

    try:
        history = _get_override_history(limit=limit)
        entries = []
        for ev in history:
            try:
                entries.append(
                    {
                        "timestamp": (
                            ev.timestamp.isoformat()
                            if hasattr(ev.timestamp, "isoformat")
                            else str(ev.timestamp)
                        ),
                        "rule_name": getattr(ev, "rule_name", "unknown"),
                        "layer": getattr(ev, "layer", "unknown"),
                        "action": getattr(
                            ev, "action_type", getattr(ev, "action", "unknown")
                        ),
                        "original_decision": getattr(ev, "original_decision", None),
                        "override_decision": getattr(ev, "override_decision", None),
                        "reason": getattr(ev, "reason", ""),
                    }
                )
            except Exception:
                entries.append({"raw": str(ev)})
        return {"available": True, "count": len(entries), "entries": entries}
    except Exception as exc:
        return {"available": False, "entries": [], "message": str(exc)}


# ---------------------------------------------------------------------------
# /v1/governance/shadow/log
# ---------------------------------------------------------------------------


@router.get("/shadow/log")
async def shadow_log(
    layer: Optional[str] = Query(default=None),
    passed: Optional[bool] = Query(default=None),
    opacity_level: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
) -> Dict[str, Any]:
    """Return shadow-channel decision log with optional filters."""
    if not _shadow_available:
        return {
            "available": False,
            "entries": [],
            "message": "shadow_channel module not loaded",
        }

    try:
        result = _query_shadow_log(
            layer=layer,
            passed=passed,
            opacity_level=opacity_level,
            limit=limit,
        )
        # LayerResult from shadow_channel — serialise metadata
        entries: List[Dict[str, Any]] = []
        if hasattr(result, "metadata") and isinstance(result.metadata, dict):
            raw = result.metadata.get("decisions", result.metadata)
        else:
            raw = []

        if isinstance(raw, list):
            for item in raw:
                if hasattr(item, "__dict__"):
                    entries.append(
                        {
                            k: (v.isoformat() if hasattr(v, "isoformat") else v)
                            for k, v in item.__dict__.items()
                        }
                    )
                elif isinstance(item, dict):
                    entries.append(item)
                else:
                    entries.append({"raw": str(item)})
        elif isinstance(raw, dict):
            entries = [raw]

        return {
            "available": True,
            "count": len(entries),
            "entries": entries,
            "shadow_log_size": (
                result.metadata.get("shadow_log_size", 0)
                if hasattr(result, "metadata") and isinstance(result.metadata, dict)
                else 0
            ),
        }
    except Exception as exc:
        return {"available": False, "entries": [], "message": str(exc)}


# ---------------------------------------------------------------------------
# /v1/governance/emergence
# ---------------------------------------------------------------------------


@router.get("/emergence")
async def emergence_patterns() -> Dict[str, Any]:
    """Return current emergence pattern analysis."""
    if not _emergence_available:
        return {
            "available": False,
            "patterns": [],
            "message": "emergence module not loaded",
        }

    try:
        result = _emergence.analyze_emergence()
        seq_patterns = _emergence.detect_sequence_pattern()
        cycle = _emergence.detect_cyclic_behavior()
        detected = seq_patterns + ([cycle] if cycle else [])

        patterns_out = []
        for p in detected:
            patterns_out.append(
                {
                    "pattern_id": getattr(p, "pattern_id", "unknown"),
                    "pattern_type": getattr(p, "pattern_type", "unknown"),
                    "confidence": getattr(p, "confidence", 0.0),
                    "description": getattr(p, "description", ""),
                }
            )

        return {
            "available": True,
            "total_patterns": len(patterns_out),
            "strong_patterns": len([p for p in patterns_out if p["confidence"] > 0.7]),
            "layer_passed": result.passed,
            "reason": result.reason,
            "patterns": patterns_out,
            "history_size": len(getattr(_emergence, "action_history", [])),
        }
    except Exception as exc:
        return {"available": False, "patterns": [], "message": str(exc)}


# ---------------------------------------------------------------------------
# /v1/governance/uplift
# ---------------------------------------------------------------------------


@router.get("/uplift")
async def uplift_status() -> Dict[str, Any]:
    """Return capability tier maturity and locked/unlocked capabilities."""
    if not _uplift_available:
        return {"available": False, "message": "uplift module not loaded"}

    try:
        locked = _get_locked()
        unlocked = _get_unlocked()

        maturity = getattr(_uplift, "maturity", None)
        maturity_dict: Dict[str, Any] = {}
        if maturity is not None:
            maturity_dict = {
                "success_count": getattr(maturity, "success_count", 0),
                "failure_count": getattr(maturity, "failure_count", 0),
                "rollback_count": getattr(maturity, "rollback_count", 0),
                "avg_confidence": getattr(maturity, "avg_confidence", 0.0),
                "success_rate": (
                    maturity.success_rate()
                    if callable(getattr(maturity, "success_rate", None))
                    else None
                ),
            }

        def _cap_dict(cap: Any) -> Dict[str, Any]:
            return {
                "name": getattr(cap, "name", str(cap)),
                "tier": (
                    getattr(cap.tier, "value", str(getattr(cap, "tier", "unknown")))
                    if hasattr(cap, "tier")
                    else "unknown"
                ),
                "description": getattr(cap, "description", ""),
                "unlocked": getattr(cap, "unlocked", False),
            }

        return {
            "available": True,
            "maturity": maturity_dict,
            "unlocked_count": len(unlocked),
            "locked_count": len(locked),
            "unlocked": [_cap_dict(c) for c in unlocked],
            "locked": [_cap_dict(c) for c in locked],
        }
    except Exception as exc:
        return {"available": False, "message": str(exc)}
