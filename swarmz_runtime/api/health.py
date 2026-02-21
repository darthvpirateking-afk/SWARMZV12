# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
"""
Consolidated health-check endpoints for the SWARMZ runtime.

Phase 3.1 modernization: all health and readiness probes live here
so that swarmz_server.py, server.py, and swarmz_runtime.api.server
no longer need to define their own copies.

Endpoints:
    GET /health                    - basic liveness probe
    GET /v1/health                 - detailed health (uptime, offline mode)
    GET /v1/observability/health   - observability liveness
    GET /v1/observability/ready    - readiness probe
"""

import os
from datetime import datetime, timezone

from fastapi import APIRouter

# ---------------------------------------------------------------------------
# Module-level start time -- captured once at import so every endpoint can
# report accurate uptime without depending on external state.
# ---------------------------------------------------------------------------
_START_TIME: datetime = datetime.now(timezone.utc)

# ---------------------------------------------------------------------------
# Offline-mode resolution follows the same precedence used by the runtime
# server: environment variable first, then config file, default False.
# ---------------------------------------------------------------------------


def _resolve_offline_mode() -> bool:
    """Return True when the runtime should operate in offline mode.

    Precedence:
        1. ``OFFLINE_MODE`` environment variable (truthy / falsy)
        2. ``config/runtime.json`` -> ``offlineMode`` key
        3. Default: ``False``
    """
    env_val = os.getenv("OFFLINE_MODE")
    if env_val is not None:
        if env_val in {"0", "false", "False", ""}:
            return False
        return True

    # Best-effort read of config/runtime.json (avoid hard dependency)
    try:
        import json
        from pathlib import Path

        cfg_path = Path(__file__).resolve().parent.parent.parent / "config" / "runtime.json"
        if cfg_path.exists():
            cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
            if isinstance(cfg, dict):
                return bool(cfg.get("offlineMode") or cfg.get("offline_mode"))
    except Exception:
        pass

    return False


OFFLINE_MODE: bool = _resolve_offline_mode()

# ---------------------------------------------------------------------------
# Router -- no prefix so that paths are expressed verbatim.
# ---------------------------------------------------------------------------
router = APIRouter(tags=["health"])


@router.get("/health")
def health_basic():
    """Basic liveness probe.

    Intentionally cheap and side-effect free so that load-balancers
    (Railway, k8s, etc.) can poll it at high frequency.
    """
    return {"ok": True, "status": "ok", "service": "swarmz-backend"}


@router.get("/v1/health")
def health_v1():
    """Detailed health check with uptime and offline-mode flag.

    Combines the information previously returned by the health endpoints
    in ``swarmz_server.py``, ``server.py``, and
    ``swarmz_runtime.api.server``.
    """
    uptime_seconds = int(
        (datetime.now(timezone.utc) - _START_TIME).total_seconds()
    )
    return {
        "ok": True,
        "status": "healthy",
        "service": "swarmz-backend",
        "uptime_seconds": uptime_seconds,
        "offline_mode": OFFLINE_MODE,
    }


@router.get("/v1/observability/health")
def observability_health():
    """Observability liveness probe.

    Must be fast and side-effect free.  Mirrors the contract
    previously in ``swarmz_runtime.api.observability`` and the
    inline definitions in ``swarmz_runtime.api.server``.
    """
    return {"status": "ok"}


@router.get("/v1/observability/ready")
def observability_ready():
    """Readiness probe.

    Returns ``ready`` once the module has been imported and the router
    is mounted.  Expand with dependency checks (DB, cache, etc.) as
    the runtime matures.
    """
    return {"status": "ready"}
