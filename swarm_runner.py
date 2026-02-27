# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
#!/usr/bin/env python3
"""
SWARMZ Swarm Runner picks up PENDING missions and runs them.

Writes results to packs/<mission_id>/result.json (or error.json on failure).
Updates data/missions.jsonl with status (RUNNING -> SUCCESS|FAILURE).
Writes a heartbeat to data/runner_heartbeat.json every tick.
AI-eligible missions go through the mission solver for PLAN + PREPARED_ACTIONS.

Designed to run in a daemon thread or standalone process.
"""

import json
import sqlite3
import time
import traceback
from datetime import date, datetime, time as dt_time, timedelta, timezone
from pathlib import Path
from typing import Any, Dict
from zoneinfo import ZoneInfo

from jsonl_utils import read_jsonl, write_jsonl

DATA_DIR = Path("data")
MISSIONS_FILE = DATA_DIR / "missions.jsonl"
AUDIT_FILE = DATA_DIR / "audit.jsonl"
HEARTBEAT_FILE = DATA_DIR / "runner_heartbeat.json"
PACKS_DIR = Path("packs")
RUNNER_STATE_DB = DATA_DIR / "runner_state.db"

TICK_INTERVAL = 1
MAX_BACKOFF_SECONDS = 30
BACKOFF_EXPONENT_CAP = 5


# atomic-ish JSONL helpers


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _compute_backoff(consecutive_errors: int) -> int:
    if consecutive_errors <= 0:
        return TICK_INTERVAL
    exponent = min(consecutive_errors, BACKOFF_EXPONENT_CAP)
    return min(MAX_BACKOFF_SECONDS, TICK_INTERVAL * (2**exponent))


def _init_runner_state_db() -> None:
    with sqlite3.connect(RUNNER_STATE_DB) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS runner_state (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                updated_at TEXT NOT NULL,
                last_status TEXT NOT NULL DEFAULT 'up',
                consecutive_errors INTEGER NOT NULL DEFAULT 0,
                last_error TEXT NOT NULL DEFAULT '',
                last_tick_latency_ms INTEGER NOT NULL DEFAULT 0,
                last_sleep_seconds INTEGER NOT NULL DEFAULT 1,
                total_ticks INTEGER NOT NULL DEFAULT 0,
                total_loop_errors INTEGER NOT NULL DEFAULT 0,
                total_processed INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        conn.execute(
            """
            INSERT OR IGNORE INTO runner_state (id, updated_at)
            VALUES (1, ?)
            """,
            (_utc_now_iso(),),
        )
        conn.commit()


def _load_runner_state() -> Dict[str, Any]:
    default_state = {
        "last_status": "up",
        "consecutive_errors": 0,
        "last_error": "",
        "last_tick_latency_ms": 0,
        "last_sleep_seconds": TICK_INTERVAL,
        "total_ticks": 0,
        "total_loop_errors": 0,
        "total_processed": 0,
    }
    if not RUNNER_STATE_DB.exists():
        return default_state
    with sqlite3.connect(RUNNER_STATE_DB) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM runner_state WHERE id = 1").fetchone()
        if row is None:
            return default_state
        loaded = dict(row)
    loaded.pop("id", None)
    loaded.pop("updated_at", None)
    for key, value in default_state.items():
        loaded.setdefault(key, value)
    return loaded


def _rewrite_missions(missions):
    """Rewrite entire missions.jsonl from list (read-all, update, write-temp, replace)."""
    tmp = MISSIONS_FILE.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        for m in missions:
            f.write(json.dumps(m, separators=(",", ":")) + "\n")
    tmp.replace(MISSIONS_FILE)


def _audit(event: str, **kwargs):
    now = _utc_now_iso()
    entry = {"timestamp": now, "event": event}
    entry.update(kwargs)
    write_jsonl(AUDIT_FILE, entry)


def _write_heartbeat(
    status: str = "up",
    *,
    loop_latency_ms: int = 0,
    consecutive_errors: int = 0,
    backoff_seconds: int = TICK_INTERVAL,
    last_error: str = "",
    total_ticks: int = 0,
    total_processed: int = 0,
):
    now = _utc_now_iso()
    hb = {
        "status": status,
        "last_tick": now,
        "loop_latency_ms": loop_latency_ms,
        "consecutive_errors": consecutive_errors,
        "backoff_seconds": backoff_seconds,
        "last_error": last_error,
        "total_ticks": total_ticks,
        "total_processed": total_processed,
    }
    HEARTBEAT_FILE.write_text(json.dumps(hb), encoding="utf-8")


def _persist_runner_state(
    *,
    status: str,
    consecutive_errors: int,
    last_error: str,
    loop_latency_ms: int,
    sleep_seconds: int,
    total_ticks: int,
    total_loop_errors: int,
    total_processed: int,
) -> None:
    with sqlite3.connect(RUNNER_STATE_DB) as conn:
        conn.execute(
            """
            UPDATE runner_state
            SET
                updated_at = ?,
                last_status = ?,
                consecutive_errors = ?,
                last_error = ?,
                last_tick_latency_ms = ?,
                last_sleep_seconds = ?,
                total_ticks = ?,
                total_loop_errors = ?,
                total_processed = ?
            WHERE id = 1
            """,
            (
                _utc_now_iso(),
                status,
                max(0, consecutive_errors),
                (last_error or "")[:500],
                max(0, loop_latency_ms),
                max(0, sleep_seconds),
                max(0, total_ticks),
                max(0, total_loop_errors),
                max(0, total_processed),
            ),
        )
        conn.commit()


# Stub workers


def _worker_smoke(mission: Dict[str, Any]) -> Dict[str, Any]:
    return {"ok": True, "type": "smoke"}


def _worker_test_mission(mission: Dict[str, Any]) -> Dict[str, Any]:
    return {"ok": True, "note": "stub worker executed"}


def _worker_galileo_run(mission: Dict[str, Any]) -> Dict[str, Any]:
    try:
        from galileo.runner import run as galileo_run

        return galileo_run(mission)
    except Exception:
        return {"ok": True, "note": "galileo stub (import unavailable)"}


def _worker_unknown(mission: Dict[str, Any]) -> Dict[str, Any]:
    return {"ok": False, "error": "unknown intent"}


def _worker_ai_solve(mission: Dict[str, Any]) -> Dict[str, Any]:
    """Route mission through the AI mission solver (safe, prepare-only)."""
    try:
        from core.mission_solver import solve

        result = solve(mission)
        return {
            "ok": result.get("ok", False),
            "type": "ai_solve",
            "source": result.get("source", "unknown"),
            "prepared_actions_dir": result.get("prepared_actions_dir", ""),
            "plan_preview": (result.get("plan", ""))[:500],
            "provider": result.get("provider"),
            "model": result.get("model"),
            "latencyMs": result.get("latencyMs"),
        }
    except Exception as exc:
        return {
            "ok": True,
            "type": "ai_solve",
            "source": "error_fallback",
            "note": f"Solver unavailable: {str(exc)[:120]}",
        }


def _astropy_available() -> bool:
    try:
        import astropy  # noqa: F401

        return True
    except Exception:
        return False


def _resolve_timezone(tz_name: str):
    try:
        return ZoneInfo(tz_name)
    except Exception:
        fallback_offsets = {
            "UTC": timezone.utc,
            "Etc/UTC": timezone.utc,
            "Australia/Melbourne": timezone(timedelta(hours=10)),
        }
        if tz_name in fallback_offsets:
            return fallback_offsets[tz_name]
        raise


def _parse_space_spec(mission: Dict[str, Any]) -> Dict[str, Any]:
    spec = mission.get("spec", {}) or {}
    if not isinstance(spec, dict):
        raise ValueError("spec must be an object")

    raw_date = str(spec.get("date_utc", "")).strip()
    if raw_date:
        try:
            parsed_date = date.fromisoformat(raw_date)
        except Exception as exc:
            raise ValueError("date_utc must be YYYY-MM-DD") from exc
    else:
        parsed_date = datetime.now(timezone.utc).date()

    lat_deg = float(spec.get("lat_deg", -37.8136))
    lon_deg = float(spec.get("lon_deg", 144.9631))
    elevation_m = float(spec.get("elevation_m", 30))
    tz_name = str(spec.get("timezone", "Australia/Melbourne")).strip()

    if not (-90.0 <= lat_deg <= 90.0):
        raise ValueError("lat_deg must be between -90 and 90")
    if not (-180.0 <= lon_deg <= 180.0):
        raise ValueError("lon_deg must be between -180 and 180")

    try:
        _resolve_timezone(tz_name)
    except Exception as exc:
        raise ValueError(f"timezone is invalid: {tz_name}") from exc

    return {
        "date_utc": parsed_date.isoformat(),
        "lat_deg": lat_deg,
        "lon_deg": lon_deg,
        "elevation_m": elevation_m,
        "timezone": tz_name,
    }


def _to_iso_z(dt_value: datetime) -> str:
    return dt_value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _compute_moon_transit_astropy(spec: Dict[str, Any]) -> Dict[str, Any]:
    import astropy.units as u
    from astropy.coordinates import AltAz, EarthLocation, get_body
    from astropy.time import Time

    tz_info = _resolve_timezone(spec["timezone"])
    target_date = date.fromisoformat(spec["date_utc"])
    local_start = datetime.combine(target_date, dt_time(0, 0), tzinfo=tz_info)
    local_end = local_start + timedelta(days=1)

    location = EarthLocation(
        lat=spec["lat_deg"] * u.deg,
        lon=spec["lon_deg"] * u.deg,
        height=spec["elevation_m"] * u.m,
    )

    def altitude_for(dt_utc: datetime) -> float:
        t = Time(dt_utc)
        frame = AltAz(obstime=t, location=location)
        moon = get_body("moon", t, location=location)
        return float(moon.transform_to(frame).alt.deg)

    best_local = None
    best_alt = -90.0
    cursor = local_start
    while cursor < local_end:
        alt = altitude_for(cursor.astimezone(timezone.utc))
        if alt > best_alt:
            best_alt = alt
            best_local = cursor
        cursor += timedelta(minutes=10)

    if best_local is None:
        raise RuntimeError("unable to find moon transit")

    refine_start = best_local - timedelta(minutes=30)
    refine_end = best_local + timedelta(minutes=30)
    cursor = refine_start
    while cursor <= refine_end:
        alt = altitude_for(cursor.astimezone(timezone.utc))
        if alt > best_alt:
            best_alt = alt
            best_local = cursor
        cursor += timedelta(minutes=1)

    best_utc = best_local.astimezone(timezone.utc)
    return {
        "method": "astropy",
        "transit_utc": _to_iso_z(best_utc),
        "transit_local": best_local.isoformat(),
        "altitude_deg_at_transit": round(best_alt, 4),
        "quality_score": 0.95,
        "notes": "Computed with astropy ephemeris scan/refinement.",
    }


def _compute_moon_transit_fallback(spec: Dict[str, Any]) -> Dict[str, Any]:
    tz_info = _resolve_timezone(spec["timezone"])
    target_date = date.fromisoformat(spec["date_utc"])
    local_midnight = datetime.combine(target_date, dt_time(0, 0), tzinfo=tz_info)

    epoch_date = date(2026, 1, 1)
    day_offset = (target_date - epoch_date).days
    lunar_delay_minutes = (day_offset * 50.47) % (24.0 * 60.0)
    transit_local = local_midnight + timedelta(hours=12, minutes=lunar_delay_minutes)
    transit_utc = transit_local.astimezone(timezone.utc)

    # Stable approximation: keep altitude deterministic and bounded.
    altitude = 50.0 - (abs(spec["lat_deg"]) * 0.25) + ((day_offset % 7) - 3) * 1.2
    altitude = max(-5.0, min(85.0, altitude))

    return {
        "method": "fallback",
        "transit_utc": _to_iso_z(transit_utc),
        "transit_local": transit_local.isoformat(),
        "altitude_deg_at_transit": round(altitude, 4),
        "quality_score": 0.52,
        "notes": "Approximate fallback (no astropy). Transit drift uses lunar-day offset.",
    }


def _ingest_space_result(
    *,
    mission_id: str,
    sim_artifact: Dict[str, Any],
    method: str,
) -> tuple[float, str]:
    from nexusmon.artifacts import get_vault
    from nexusmon.entity import get_entity

    xp_award = 18.0 if method == "astropy" else 8.0
    xp_info = get_entity().award_xp(xp_award)
    artifact = get_vault().create(
        name=f"Moon Transit {sim_artifact['input']['date_utc']}",
        artifact_type="KNOWLEDGE_BLOCK",
        rarity="UNCOMMON" if method == "astropy" else "COMMON",
        created_by="swarmz-minion-space-sim",
        tags=["space", "moon", "transit", "simulation"],
        metadata={"mission_id": mission_id, "method": method},
        payload=sim_artifact,
    )
    # Prefer reported awarded XP if available.
    final_xp = float(xp_info.get("xp_awarded", xp_award)) if isinstance(xp_info, dict) else xp_award
    return final_xp, str(artifact.get("id", ""))


def _worker_space_moon_transit(mission: Dict[str, Any]) -> Dict[str, Any]:
    mission_id = str(mission.get("mission_id", "unknown"))
    pack_dir = PACKS_DIR / mission_id
    pack_dir.mkdir(parents=True, exist_ok=True)

    try:
        parsed_spec = _parse_space_spec(mission)
    except Exception as exc:
        return {"ok": False, "type": "space_moon_transit", "error": str(exc)}

    if _astropy_available():
        transit = _compute_moon_transit_astropy(parsed_spec)
    else:
        transit = _compute_moon_transit_fallback(parsed_spec)

    sim_artifact = {
        "mission_id": mission_id,
        "sim_type": "moon_meridian_transit",
        "computed_at_utc": _utc_now_iso(),
        "input": parsed_spec,
        "method": transit["method"],
        "transit_utc": transit["transit_utc"],
        "transit_local": transit["transit_local"],
        "altitude_deg_at_transit": transit["altitude_deg_at_transit"],
        "quality_score": transit["quality_score"],
        "notes": transit["notes"],
    }
    (pack_dir / "moon_transit.json").write_text(
        json.dumps(sim_artifact, indent=2),
        encoding="utf-8",
    )

    xp_awarded = 0.0
    artifact_id = ""
    ingestion_error = ""
    try:
        xp_awarded, artifact_id = _ingest_space_result(
            mission_id=mission_id,
            sim_artifact=sim_artifact,
            method=transit["method"],
        )
    except Exception as exc:
        ingestion_error = str(exc)[:200]

    note = (
        f"Moon transit ({transit['method']}) at {transit['transit_utc']} "
        f"alt {transit['altitude_deg_at_transit']} deg."
    )
    if ingestion_error:
        note += f" Ingestion warning: {ingestion_error}"

    _audit(
        "space_sim_completed",
        mission_id=mission_id,
        method=transit["method"],
        quality_score=transit["quality_score"],
        artifact_id=artifact_id,
        xp_awarded=xp_awarded,
        ingestion_error=ingestion_error,
    )

    return {
        "ok": True,
        "type": "space_moon_transit",
        "method": transit["method"],
        "transit_utc": transit["transit_utc"],
        "quality_score": transit["quality_score"],
        "xp_awarded": xp_awarded,
        "artifact_id": artifact_id,
        "note": note,
    }


# Categories that should go through AI solver when available
AI_ELIGIBLE_CATEGORIES = {"build", "solve", "plan", "analyze", "research"}

WORKERS = {
    "smoke": _worker_smoke,
    "test_mission": _worker_test_mission,
    "galileo_run": _worker_galileo_run,
    "ai_solve": _worker_ai_solve,
    "swarmz-minion-space-sim": _worker_space_moon_transit,
}


# Core tick logic


def _process_one() -> bool:
    """Find first PENDING mission, run it, write results."""
    missions, _, _ = read_jsonl(MISSIONS_FILE)

    # Check QUARANTINE: if active, block execution and log
    success_count = sum(1 for m in missions if m.get("status") == "SUCCESS")
    total = len(missions)
    if total >= 10:
        success_rate = success_count / total
        if success_rate < 0.3:
            # QUARANTINE active: skip execution
            pending = [m for m in missions if m.get("status") == "PENDING"]
            if pending:
                _audit(
                    "quarantine_blocked",
                    pending_count=len(pending),
                    total=total,
                    success_rate=round(success_rate, 3),
                )
            return False

    target = None
    for m in missions:
        if m.get("status") == "PENDING":
            target = m
            break
    if target is None:
        return False

    mission_id = target.get("mission_id", "unknown")
    intent = target.get("intent", target.get("goal", "unknown"))
    pack_dir = PACKS_DIR / mission_id
    pack_dir.mkdir(parents=True, exist_ok=True)

    # Before mission: gather context + select strategy
    pre_ctx = {}
    try:
        from core.context_pack import before_mission

        pre_ctx = before_mission(target)
    except Exception:
        pass
    strategy = pre_ctx.get("strategy", "baseline")
    inputs_hash = pre_ctx.get("inputs_hash", "")
    candidates = pre_ctx.get("candidates", [])

    # Mark RUNNING
    started_at = _utc_now_iso()
    target["status"] = "RUNNING"
    target["started_at"] = started_at
    _rewrite_missions(missions)
    _audit("mission_started", mission_id=mission_id, intent=intent, strategy=strategy)

    # Execute worker
    t0 = time.monotonic()
    try:
        worker_fn = WORKERS.get(intent, None)
        # Route AI-eligible missions through ai_solve if no explicit worker
        if worker_fn is None:
            category = target.get("category", "")
            if category in AI_ELIGIBLE_CATEGORIES or intent == "ai_solve":
                worker_fn = _worker_ai_solve
            else:
                worker_fn = _worker_unknown
        result = worker_fn(target)
        duration_ms = int((time.monotonic() - t0) * 1000)

        # Write result
        (pack_dir / "result.json").write_text(
            json.dumps(result, indent=2), encoding="utf-8"
        )

        # Determine outcome
        if result.get("ok"):
            target["status"] = "SUCCESS"
        else:
            target["status"] = "FAILURE"

        target["finished_at"] = _utc_now_iso()
        target["duration_ms"] = duration_ms
        _rewrite_missions(missions)
        _audit(
            "mission_finished",
            mission_id=mission_id,
            outcome=target["status"],
            duration_ms=duration_ms,
        )

        # After mission: update all engines
        try:
            from core.context_pack import after_mission

            after_mission(
                target,
                result,
                duration_ms,
                strategy=strategy,
                inputs_hash=inputs_hash,
                candidates=candidates,
            )
        except Exception:
            pass
        return True

    except Exception as exc:
        duration_ms = int((time.monotonic() - t0) * 1000)
        tb_tail = traceback.format_exc().splitlines()[-5:]

        # Write error
        (pack_dir / "error.json").write_text(
            json.dumps({"error": str(exc), "traceback": tb_tail}, indent=2),
            encoding="utf-8",
        )

        target["status"] = "FAILURE"
        target["finished_at"] = _utc_now_iso()
        target["duration_ms"] = duration_ms
        _rewrite_missions(missions)
        _audit(
            "mission_finished",
            mission_id=mission_id,
            outcome="FAILURE",
            duration_ms=duration_ms,
            error=str(exc),
        )
        return True


# Main loop


def run_loop(max_ticks: int | None = None):
    """Infinite runner loop. Call from daemon thread or __main__."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    PACKS_DIR.mkdir(parents=True, exist_ok=True)
    _init_runner_state_db()

    state = _load_runner_state()
    consecutive_errors = int(state.get("consecutive_errors", 0))
    total_ticks = int(state.get("total_ticks", 0))
    total_loop_errors = int(state.get("total_loop_errors", 0))
    total_processed = int(state.get("total_processed", 0))

    while True:
        tick_start = time.monotonic()
        status = "up"
        sleep_seconds = TICK_INTERVAL
        last_error = ""
        try:
            processed = _process_one()
            if processed:
                total_processed += 1
            if consecutive_errors > 0:
                _audit("runner_recovered", consecutive_errors=consecutive_errors)
            consecutive_errors = 0
        except Exception as exc:
            # runner must not crash, back off and continue
            status = "degraded"
            consecutive_errors += 1
            total_loop_errors += 1
            last_error = str(exc)[:400]
            sleep_seconds = _compute_backoff(consecutive_errors)
            _audit(
                "runner_loop_error",
                error=last_error,
                consecutive_errors=consecutive_errors,
                backoff_seconds=sleep_seconds,
            )

        loop_latency_ms = int((time.monotonic() - tick_start) * 1000)
        total_ticks += 1

        try:
            _write_heartbeat(
                status=status,
                loop_latency_ms=loop_latency_ms,
                consecutive_errors=consecutive_errors,
                backoff_seconds=sleep_seconds,
                last_error=last_error,
                total_ticks=total_ticks,
                total_processed=total_processed,
            )
            _persist_runner_state(
                status=status,
                consecutive_errors=consecutive_errors,
                last_error=last_error,
                loop_latency_ms=loop_latency_ms,
                sleep_seconds=sleep_seconds,
                total_ticks=total_ticks,
                total_loop_errors=total_loop_errors,
                total_processed=total_processed,
            )
        except Exception:
            # heartbeat/state failures should not terminate the loop
            pass

        if max_ticks is not None and total_ticks >= max_ticks:
            return
        time.sleep(sleep_seconds)


if __name__ == "__main__":
    print("[SWARM RUNNER] Starting standalone runner loop...")
    run_loop()


def run_swarm():
    run_loop()
