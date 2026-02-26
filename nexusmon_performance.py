"""
NEXUSMON — Performance Optimizations
=====================================

1. GZip middleware — compresses all responses >500 bytes (~60-80% smaller)
2. /v1/cockpit/snapshot — one fetch replaces 5+ tab-load calls
3. cached() decorator — 5s TTL for hot reads (available for use in other modules)

Fusion: fuse_performance(app)
"""

import time
import functools
from typing import Optional
from fastapi import APIRouter
from fastapi.middleware.gzip import GZipMiddleware


# ─── Caching Decorator ───────────────────────────────────────────────────────

_cache: dict = {}


def cached(key: str, ttl: float = 5.0):
    """
    In-memory cache with TTL. Apply to any pure read function.

    Usage:
        @cached("operator_rank", ttl=5)
        def get_operator_rank_state():
            ...
    """
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            now = time.time()
            if key in _cache and now - _cache[key][1] < ttl:
                return _cache[key][0]
            result = fn(*args, **kwargs)
            _cache[key] = (result, now)
            return result
        return wrapper
    return decorator


def invalidate_cache(key: Optional[str] = None):
    """Clear a specific cache key, or all keys if none given."""
    if key:
        _cache.pop(key, None)
    else:
        _cache.clear()


# ─── Cockpit Snapshot ────────────────────────────────────────────────────────

router = APIRouter(tags=["performance"])


@router.get("/v1/cockpit/snapshot")
async def cockpit_snapshot():
    """
    Single endpoint returning all cockpit data.
    Replaces 5+ separate API calls on tab load.

    Keys: operator, organism, missions, vault, cognition
    """
    result: dict = {}

    # Operator rank state
    try:
        from nexusmon_operator_rank import get_operator_rank_state
        result["operator"] = get_operator_rank_state()
    except Exception as e:
        result["operator"] = {"error": str(e)}

    # Organism: evolution + operator context + workers + claimlab
    try:
        from nexusmon_organism import evo_status, ctx_status, _load_jsonl, _data_dir, _beliefs_path
        from pathlib import Path
        workers = _load_jsonl(_data_dir() / "workers.jsonl")
        active = [w for w in workers if w.get("status") == "RUNNING"]
        beliefs = _load_jsonl(_beliefs_path())
        result["organism"] = {
            "ok": True,
            "evolution": evo_status(),
            "operator": ctx_status(),
            "workers": {
                "active_count": len(active),
                "active": active[-3:],
                "total": len(workers),
            },
            "claimlab": {
                "belief_count": len([b for b in beliefs if b.get("status") == "active"])
            },
        }
    except Exception as e:
        result["organism"] = {"error": str(e)}

    # Mission stats (sync function)
    try:
        from nexusmon_mission_engine import get_stats as _mission_stats
        result["missions"] = _mission_stats()
    except Exception as e:
        result["missions"] = {"error": str(e)}

    # Vault stats (sync function)
    try:
        from nexusmon_artifact_vault import get_stats as _vault_stats
        result["vault"] = _vault_stats()
    except Exception as e:
        result["vault"] = {"error": str(e)}

    # Cognition status
    try:
        from nexusmon_cognition import cognition_status as _cog_status
        result["cognition"] = await _cog_status()
    except Exception as e:
        result["cognition"] = {"error": str(e)}

    return result


# ─── Fusion ──────────────────────────────────────────────────────────────────

def fuse_performance(app):
    """
    Mount performance optimizations into the FastAPI app.

    Add to swarmz_server.py alongside other fuse calls:

        try:
            from nexusmon_performance import fuse_performance
            fuse_performance(app)
        except Exception as e:
            print(f"[WARN] Performance not loaded: {e}")
    """
    # GZip compresses all responses > 500 bytes — free 60-80% size reduction
    app.add_middleware(GZipMiddleware, minimum_size=500)

    # Snapshot endpoint
    app.include_router(router)

    print("[NEXUSMON] Performance fused — GZip enabled, /v1/cockpit/snapshot live.")
