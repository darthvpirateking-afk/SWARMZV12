# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
#!/usr/bin/env python3
"""
verification_runner.py – Post-action verification with automatic rollback.

Behaviour:
  * Listens for ``ACTION_SELECTED`` events.
  * Stores a baseline metric snapshot.
  * Waits until the verification deadline.
  * Checks the metric against the action's verification spec.
  * Emits ``VERIFY_PASSED`` or ``VERIFY_FAILED``.
  * On failure, auto-publishes the rollback action.
  * All outcomes are appended to verification_log.jsonl.

Usage (async entry-point)::

    python verification_runner.py                    # run service
    python verification_runner.py --pg-dsn postgres://...

Fallback (in-process, no Postgres) for dev/test::

    from verification_runner import VerificationRunner
    runner = VerificationRunner(store, vstore, bus, adapter)
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import sys
import time
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any

_DIR = os.path.dirname(os.path.abspath(__file__))
_PARENT = os.path.dirname(_DIR)
if _PARENT not in sys.path:
    sys.path.insert(0, _PARENT)

from control_plane.state_store import StateStore
from control_plane.verification_store import VerificationStore
from control_plane.event_debouncer import EventDebouncer
from control_plane.swarmz_adapter import SwarmzAdapter
from control_plane.expression_eval import evaluate
from control_plane.decision_logger import DecisionLogger

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Job status literals (state machine)
STATUS_QUEUED = "QUEUED"
STATUS_WAITING = "WAITING"
STATUS_PASSED = "PASSED"
STATUS_FAILED = "FAILED"
STATUS_EXPIRED = "EXPIRED"
STATUS_CANCELLED = "CANCELLED"
STATUS_DEADLETTERED = "DEADLETTERED"

_TERMINAL = frozenset({STATUS_PASSED, STATUS_FAILED, STATUS_EXPIRED,
                       STATUS_CANCELLED, STATUS_DEADLETTERED})

# Default limits
DEFAULT_MAX_ATTEMPTS = 3
DEFAULT_LEASE_SECONDS = 60
HEARTBEAT_INTERVAL_SECONDS = 30

# Load actions catalogue for rollback lookup
_ACTIONS_PATH = os.path.join(_DIR, "data", "actions.json")
with open(_ACTIONS_PATH) as _f:
    _ACTIONS: list[dict] = json.load(_f)
_ACTIONS_BY_ID: dict[str, dict] = {a["action_id"]: a for a in _ACTIONS}

# State file path (for byte-offset delta evaluation)
_STATE_JSONL = os.path.join(_DIR, "data", "state.jsonl")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sha256(*parts: str) -> str:
    """Deterministic hash of pipe-joined string parts."""
    return hashlib.sha256("|".join(parts).encode()).hexdigest()


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _now_iso() -> str:
    return _now_utc().isoformat()


def _make_dedupe_key(decision_id: str, action_id: str,
                     verify_spec_hash: str) -> str:
    return _sha256(decision_id, action_id, verify_spec_hash)


def _hash_verify_spec(spec: dict) -> str:
    canonical = json.dumps(spec, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


def _state_file_offset(path: str = _STATE_JSONL) -> int:
    """Return the current byte length of state.jsonl (or 0 if missing)."""
    try:
        return os.path.getsize(path)
    except OSError:
        return 0


def _read_state_records_from_offset(
    offset: int, path: str = _STATE_JSONL
) -> list[dict]:
    """Read state records starting at *offset* bytes."""
    records: list[dict] = []
    try:
        with open(path, "rb") as fh:
            fh.seek(offset)
            for raw_line in fh:
                line = raw_line.decode("utf-8", errors="replace").strip()
                if line:
                    records.append(json.loads(line))
    except (OSError, json.JSONDecodeError):
        pass
    return records


# ---------------------------------------------------------------------------
# In-memory job store (dev/test fallback – no Postgres required)
# ---------------------------------------------------------------------------

class _InMemoryJobStore:
    """Dict-backed job store used when Postgres is unavailable.

    Thread-safe via a simple lock.  Good enough for single-runner
    dev/test usage while preserving the full job state-machine.
    """

    def __init__(self):
        self._jobs: dict[str, dict] = {}          # job_id → job
        self._dedupe: dict[str, str] = {}          # dedupe_key → job_id
        self._outcomes: list[dict] = []
        import threading
        self._lock = threading.Lock()

    # -- enqueue (idempotent) -----------------------------------------------

    def enqueue(self, job: dict) -> dict:
        """Insert a new job or return the existing one (idempotent)."""
        dk = job["dedupe_key"]
        with self._lock:
            if dk in self._dedupe:
                return self._jobs[self._dedupe[dk]]
            jid = job.get("job_id") or str(uuid.uuid4())
            job["job_id"] = jid
            job.setdefault("status", STATUS_QUEUED)
            job.setdefault("attempts", 0)
            job.setdefault("created_at", _now_iso())
            job.setdefault("updated_at", _now_iso())
            job.setdefault("lease_owner", None)
            job.setdefault("lease_expires_at", None)
            job.setdefault("final_outcome_emitted_at", None)
            job.setdefault("rollback_triggered_at", None)
            job.setdefault("rollback_action_id", None)
            job.setdefault("last_error", None)
            self._jobs[jid] = job
            self._dedupe[dk] = jid
        return job

    # -- next deadline ------------------------------------------------------

    def next_deadline(self) -> datetime | None:
        with self._lock:
            candidates = [
                datetime.fromisoformat(j["deadline_at"])
                for j in self._jobs.values()
                if j["status"] in (STATUS_QUEUED, STATUS_WAITING)
            ]
        return min(candidates) if candidates else None

    # -- claim due jobs -----------------------------------------------------

    def claim_due(self, runner_id: str, lease_seconds: int,
                  now: datetime | None = None) -> list[dict]:
        now = now or _now_utc()
        claimed: list[dict] = []
        with self._lock:
            for j in self._jobs.values():
                if j["status"] not in (STATUS_QUEUED, STATUS_WAITING):
                    continue
                dl = datetime.fromisoformat(j["deadline_at"])
                if dl > now:
                    continue
                # Check lease
                if j["lease_owner"] and j["lease_expires_at"]:
                    le = datetime.fromisoformat(j["lease_expires_at"])
                    if le > now:
                        continue  # still leased by another runner
                j["lease_owner"] = runner_id
                j["lease_expires_at"] = (
                    now + timedelta(seconds=lease_seconds)
                ).isoformat()
                j["status"] = STATUS_WAITING
                j["attempts"] = j.get("attempts", 0) + 1
                j["updated_at"] = _now_iso()
                claimed.append(dict(j))
        return claimed

    # -- finalize -----------------------------------------------------------

    def finalize(self, job_id: str, runner_id: str, status: str,
                 event_type: str, error: str | None = None) -> bool:
        """Set final outcome (exactly-once guard)."""
        with self._lock:
            j = self._jobs.get(job_id)
            if not j:
                return False
            if j.get("final_outcome_emitted_at"):
                return False          # already finalized
            if j.get("lease_owner") != runner_id:
                return False          # not our lease
            j["status"] = status
            j["final_status"] = status
            j["final_outcome_emitted_at"] = _now_iso()
            j["final_outcome_event_type"] = event_type
            if error:
                j["last_error"] = error
            j["updated_at"] = _now_iso()
        return True

    # -- rollback guard -----------------------------------------------------

    def mark_rollback_triggered(self, job_id: str, runner_id: str,
                                rollback_action_id: str) -> bool:
        with self._lock:
            j = self._jobs.get(job_id)
            if not j:
                return False
            if j.get("rollback_triggered_at"):
                return False          # already triggered
            if j.get("lease_owner") != runner_id:
                return False
            j["rollback_triggered_at"] = _now_iso()
            j["rollback_action_id"] = rollback_action_id
            j["updated_at"] = _now_iso()
        return True

    # -- record rollback result ---------------------------------------------

    def record_rollback_result(self, rollback_action_id: str,
                               result: dict) -> bool:
        with self._lock:
            for j in self._jobs.values():
                if j.get("rollback_action_id") == rollback_action_id:
                    j.setdefault("rollback_result", result)
                    j["updated_at"] = _now_iso()
                    return True
        return False

    # -- dead-letter --------------------------------------------------------

    def dead_letter(self, job_id: str, runner_id: str,
                    error: str) -> bool:
        return self.finalize(job_id, runner_id, STATUS_DEADLETTERED,
                             "DEADLETTERED", error=error)

    # -- append outcome -----------------------------------------------------

    def append_outcome(self, outcome: dict):
        with self._lock:
            self._outcomes.append(outcome)

    # -- query helpers ------------------------------------------------------

    def get_job(self, job_id: str) -> dict | None:
        return self._jobs.get(job_id)

    def pending_count(self) -> int:
        with self._lock:
            return sum(1 for j in self._jobs.values()
                       if j["status"] in (STATUS_QUEUED, STATUS_WAITING))

    def stats(self) -> dict[str, int]:
        with self._lock:
            counts: dict[str, int] = {}
            for j in self._jobs.values():
                counts[j["status"]] = counts.get(j["status"], 0) + 1
        return counts


# ---------------------------------------------------------------------------
# Postgres-backed job store
# ---------------------------------------------------------------------------

class _PgJobStore:
    """Postgres-backed job store using asyncpg.

    All writes are transactional; claims use ``FOR UPDATE SKIP LOCKED``
    for multi-runner safety.
    """

    def __init__(self, pool):
        self._pool = pool

    # -- enqueue (idempotent) -----------------------------------------------

    async def enqueue(self, job: dict) -> dict:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO verification_jobs (
                    dedupe_key, decision_id, action_id, action_type,
                    config_hash, trace_id, selected_at, deadline_at,
                    baseline_state_offset, verify_spec, verify_spec_hash,
                    rollback_action_type, rollback_params, target,
                    status, max_attempts
                ) VALUES (
                    $1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16
                )
                ON CONFLICT (dedupe_key) DO NOTHING
                RETURNING job_id, status, created_at
                """,
                job["dedupe_key"], job["decision_id"], job["action_id"],
                job["action_type"], job.get("config_hash", ""),
                job.get("trace_id"),
                datetime.fromisoformat(job["selected_at"]),
                datetime.fromisoformat(job["deadline_at"]),
                job.get("baseline_state_offset", 0),
                json.dumps(job["verify_spec"]),
                job["verify_spec_hash"],
                job.get("rollback_action_type"),
                json.dumps(job.get("rollback_params", {})),
                json.dumps(job.get("target", {})),
                STATUS_QUEUED,
                job.get("max_attempts", DEFAULT_MAX_ATTEMPTS),
            )
            if row:
                job["job_id"] = str(row["job_id"])
                await conn.execute("SELECT pg_notify('vr_jobs', $1)",
                                   job["job_id"])
            else:
                existing = await conn.fetchrow(
                    "SELECT job_id FROM verification_jobs "
                    "WHERE dedupe_key = $1", job["dedupe_key"])
                job["job_id"] = str(existing["job_id"]) if existing else None
        return job

    # -- next deadline ------------------------------------------------------

    async def next_deadline(self) -> datetime | None:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT MIN(deadline_at) AS d FROM verification_jobs "
                "WHERE status IN ('QUEUED','WAITING')")
            return row["d"] if row and row["d"] else None

    # -- claim due jobs (SKIP LOCKED) ---------------------------------------

    async def claim_due(self, runner_id: str, lease_seconds: int,
                        now: datetime | None = None) -> list[dict]:
        now = now or _now_utc()
        lease_until = now + timedelta(seconds=lease_seconds)
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                UPDATE verification_jobs
                   SET lease_owner = $1,
                       lease_expires_at = $2,
                       status = 'WAITING',
                       attempts = attempts + 1
                 WHERE job_id IN (
                    SELECT job_id FROM verification_jobs
                     WHERE status IN ('QUEUED','WAITING')
                       AND deadline_at <= $3
                       AND (lease_expires_at IS NULL
                            OR lease_expires_at < $3)
                       AND attempts < max_attempts
                     ORDER BY deadline_at
                     FOR UPDATE SKIP LOCKED
                 )
                 RETURNING *
                """, runner_id, lease_until, now)
            return [dict(r) for r in rows]

    # -- finalize (exactly-once) --------------------------------------------

    async def finalize(self, job_id: str, runner_id: str, status: str,
                       event_type: str, error: str | None = None) -> bool:
        async with self._pool.acquire() as conn:
            result = await conn.execute(
                """
                UPDATE verification_jobs
                   SET status = $3,
                       final_status = $3,
                       final_outcome_emitted_at = now(),
                       final_outcome_event_type = $4,
                       last_error = COALESCE($5, last_error)
                 WHERE job_id = $1::uuid
                   AND lease_owner = $2
                   AND final_outcome_emitted_at IS NULL
                """, job_id, runner_id, status, event_type, error)
            return result == "UPDATE 1"

    # -- rollback guard (exactly-once) --------------------------------------

    async def mark_rollback_triggered(self, job_id: str, runner_id: str,
                                      rollback_action_id: str) -> bool:
        async with self._pool.acquire() as conn:
            result = await conn.execute(
                """
                UPDATE verification_jobs
                   SET rollback_triggered_at = now(),
                       rollback_action_id = $3
                 WHERE job_id = $1::uuid
                   AND lease_owner = $2
                   AND rollback_triggered_at IS NULL
                """, job_id, runner_id, rollback_action_id)
            return result == "UPDATE 1"

    # -- record rollback result ---------------------------------------------

    async def record_rollback_result(self, rollback_action_id: str,
                                     result: dict) -> bool:
        async with self._pool.acquire() as conn:
            res = await conn.execute(
                """
                UPDATE verification_jobs
                   SET target = target || $2::jsonb
                 WHERE rollback_action_id = $1
                """, rollback_action_id,
                json.dumps({"rollback_result": result}))
            return res == "UPDATE 1"

    # -- dead-letter --------------------------------------------------------

    async def dead_letter(self, job_id: str, runner_id: str,
                          error: str) -> bool:
        return await self.finalize(job_id, runner_id, STATUS_DEADLETTERED,
                                   "DEADLETTERED", error=error)

    # -- append outcome (append-only ledger) --------------------------------

    async def append_outcome(self, outcome: dict):
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO verification_outcomes
                    (job_id, decision_id, action_id, status, payload)
                VALUES ($1::uuid, $2, $3, $4, $5)
                """,
                outcome["job_id"], outcome["decision_id"],
                outcome["action_id"], outcome["status"],
                json.dumps(outcome.get("payload", {})))

    # -- query helpers ------------------------------------------------------

    async def pending_count(self) -> int:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT count(*) AS c FROM verification_jobs "
                "WHERE status IN ('QUEUED','WAITING')")
            return row["c"]

    async def stats(self) -> dict[str, int]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT status, count(*) AS c FROM verification_jobs "
                "GROUP BY status")
            return {r["status"]: r["c"] for r in rows}


# ---------------------------------------------------------------------------
# Delta evaluator
# ---------------------------------------------------------------------------

class DeltaEvaluator:
    """Evaluates verification metric deltas from ``state.jsonl``.

    Reads records written *after* ``baseline_state_offset`` bytes and
    applies deterministic aggregation (mean for MVP).
    """

    def __init__(self, state_path: str = _STATE_JSONL):
        self._path = state_path

    def evaluate(self, job: dict) -> dict:
        """Return ``{passed, baseline, actual, delta, failure_reason}``."""
        spec = job["verify_spec"]
        metric = spec["metric"]
        op = spec["operator"]
        threshold = spec["threshold"]
        offset = job.get("baseline_state_offset", 0)

        # Read records after baseline offset
        records = _read_state_records_from_offset(offset, self._path)
        metric_vals = [
            r["value"] for r in records
            if r.get("variable") == metric and r.get("value") is not None
        ]

        # Baseline: latest value *before* offset (use StateStore for O(1))
        baseline = job.get("_baseline_value")

        if not metric_vals:
            return {
                "passed": False,
                "baseline": baseline,
                "actual": None,
                "delta": None,
                "failure_reason": "missing_metric",
            }

        # Deterministic aggregator: mean
        actual = sum(metric_vals) / len(metric_vals)
        delta = (actual - baseline) if baseline is not None else None

        try:
            passed = evaluate(op, actual, threshold)
        except ValueError:
            return {
                "passed": False,
                "baseline": baseline,
                "actual": actual,
                "delta": delta,
                "failure_reason": "unknown_op",
            }

        return {
            "passed": passed,
            "baseline": baseline,
            "actual": actual,
            "delta": delta,
            "failure_reason": None if passed else "threshold_not_met",
        }


# ---------------------------------------------------------------------------
# VerificationRunner (unified: in-memory or Postgres)
# ---------------------------------------------------------------------------

class VerificationRunner:
    """Verifies executed actions and triggers rollback on failure.

    Works in two modes:

    * **In-process** (no Postgres): uses ``_InMemoryJobStore`` and the
      existing ``EventDebouncer`` for pub/sub.  Suitable for dev/test.
    * **Postgres-backed** (production): uses ``_PgJobStore`` with
      LISTEN/NOTIFY for wakeups and lease-based claiming.
    """

    def __init__(
        self,
        store: StateStore,
        vstore: VerificationStore,
        bus: EventDebouncer,
        adapter: SwarmzAdapter,
        *,
        runner_id: str | None = None,
        pg_pool=None,
        decision_logger: DecisionLogger | None = None,
        max_attempts: int = DEFAULT_MAX_ATTEMPTS,
        lease_seconds: int = DEFAULT_LEASE_SECONDS,
    ):
        self._state = store
        self._vstore = vstore
        self._bus = bus
        self._adapter = adapter
        self._runner_id = runner_id or f"vr-{uuid.uuid4().hex[:8]}"
        self._max_attempts = max_attempts
        self._lease_seconds = lease_seconds
        self._decision_logger = decision_logger or DecisionLogger()
        self._evaluator = DeltaEvaluator(
            state_path=store.path if hasattr(store, 'path') else _STATE_JSONL
        )

        # Metrics counters
        self._metrics: dict[str, int] = {
            "enqueued": 0, "passed": 0, "failed": 0,
            "expired": 0, "deadlettered": 0, "rollbacks": 0,
        }

        # Choose job store backend
        if pg_pool is not None:
            self._jobs: Any = _PgJobStore(pg_pool)
            self._async_mode = True
        else:
            self._jobs = _InMemoryJobStore()
            self._async_mode = False

        # Subscribe to events
        bus.subscribe("ACTION_SELECTED", self._on_action_selected)
        bus.subscribe("ACT_RESULT", self._on_act_result)
        bus.subscribe("ACTION_TAKEN", self._on_act_result)

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _on_action_selected(self, _event: str, action: dict):
        """Enqueue a verification job idempotently."""
        if action is None:
            return
        vspec = action.get("verification")
        if not vspec:
            return

        decision_id = action.get("decision_id", action.get("action_id", ""))
        action_id = action.get("action_id", "")
        action_type = action.get("action_type", action.get("layer", ""))
        spec_hash = _hash_verify_spec(vspec)
        dedupe_key = _make_dedupe_key(decision_id, action_id, spec_hash)

        now = _now_utc()
        deadline = now + timedelta(
            seconds=vspec.get("deadline_seconds", 30))

        baseline_offset = _state_file_offset(self._evaluator._path)
        baseline_value = self._state.get_value(vspec["metric"])

        rb_spec = action.get("rollback", {})

        job = {
            "dedupe_key": dedupe_key,
            "decision_id": decision_id,
            "action_id": action_id,
            "action_type": action_type,
            "config_hash": action.get("config_hash", ""),
            "trace_id": action.get("trace_id"),
            "selected_at": now.isoformat(),
            "deadline_at": deadline.isoformat(),
            "baseline_state_offset": baseline_offset,
            "verify_spec": vspec,
            "verify_spec_hash": spec_hash,
            "rollback_action_type": rb_spec.get("action_id"),
            "rollback_params": rb_spec,
            "target": action.get("target", {}),
            "max_attempts": self._max_attempts,
            # Carry baseline value for the evaluator
            "_baseline_value": baseline_value,
        }

        if self._async_mode:
            # Postgres enqueue must be awaited; schedule via event loop
            asyncio.ensure_future(self._async_enqueue(job))
        else:
            self._jobs.enqueue(job)
            self._metrics["enqueued"] += 1

    async def _async_enqueue(self, job: dict):
        await self._jobs.enqueue(job)
        self._metrics["enqueued"] += 1

    def _on_act_result(self, _event: str, result: dict):
        """Correlate rollback ACT results back to jobs."""
        if result is None:
            return
        rb_aid = result.get("action_id", "")
        if self._async_mode:
            asyncio.ensure_future(
                self._jobs.record_rollback_result(rb_aid, result))
        else:
            self._jobs.record_rollback_result(rb_aid, result)
        # Defer event emission to avoid re-entrant lock in EventDebouncer
        import threading
        threading.Timer(
            0, self._bus.publish,
            args=("ROLLBACK_RESULT_RECORDED", result),
        ).start()

    # ------------------------------------------------------------------
    # Synchronous check (in-process / dev mode)
    # ------------------------------------------------------------------

    def check_pending(self):
        """Claim and evaluate all due jobs (synchronous, in-process mode)."""
        if self._async_mode:
            raise RuntimeError(
                "Use run_async() for Postgres-backed mode")

        now = _now_utc()
        claimed = self._jobs.claim_due(
            self._runner_id, self._lease_seconds, now)

        for job in claimed:
            max_att = job.get("max_attempts", self._max_attempts)
            if job["attempts"] > max_att:
                self._do_dead_letter(job, "max_attempts_exceeded")
                continue

            # Deadline reached – evaluate
            actual = self._state.get_value(vspec["metric"])
            passed = False
            if actual is not None:
                passed = evaluate(vspec["operator"], actual, vspec["threshold"])

            log_entry = {
                "action_id": action["action_id"],
                "metric": vspec["metric"],
                "baseline": item["baseline"],
                "actual": actual,
                "threshold": vspec["threshold"],
                "operator": vspec["operator"],
                "passed": passed,
            }

            if passed:
                log_entry["outcome"] = "VERIFY_PASSED"
                self._bus.publish("VERIFY_PASSED", log_entry)
                print(f"[verify] PASSED: {action['action_id']}")
            else:
                log_entry["outcome"] = "VERIFY_FAILED"
                self._bus.publish("VERIFY_FAILED", log_entry)
                print(f"[verify] FAILED: {action['action_id']} – triggering rollback")
                self._do_rollback(action)

            self._vstore.log(log_entry)

        self._pending = still_pending

    def _do_rollback(self, job: dict):
        """Trigger rollback (exactly-once guard)."""
        rb_type = job.get("rollback_action_type")
        rb_action = _ACTIONS_BY_ID.get(rb_type) if rb_type else None
        if not rb_action:
            print(f"[verify] no rollback action for {job['action_id']}")
            return

        rb_action_id = f"rb-{job['job_id']}-{uuid.uuid4().hex[:8]}"

        marked = self._jobs.mark_rollback_triggered(
            job["job_id"], self._runner_id, rb_action_id)
        if not marked:
            return  # Already triggered

        self._adapter.execute(rb_action)
        self._metrics["rollbacks"] += 1

        rb_payload = {
            "job_id": job["job_id"],
            "decision_id": job["decision_id"],
            "action_id": job["action_id"],
            "rollback_action_id": rb_action_id,
            "rollback_action_type": rb_type,
            "rollback_params": job.get("rollback_params", {}),
            "triggered_at": _now_iso(),
            "config_hash": job.get("config_hash", ""),
            "trace_id": job.get("trace_id"),
        }
        self._bus.publish("ROLLBACK_TRIGGERED", rb_payload)
        print(f"[verify] rollback triggered: {rb_type}")

    # ------------------------------------------------------------------
    # Decision log + calibration
    # ------------------------------------------------------------------

    def _build_outcome_payload(self, job: dict, result: dict,
                               outcome: str) -> dict:
        spec = job["verify_spec"]
        return {
            "job_id": job["job_id"],
            "decision_id": job["decision_id"],
            "action_id": job["action_id"],
            "action_type": job.get("action_type", ""),
            "outcome": outcome,
            "verify_spec_hash": job.get("verify_spec_hash", ""),
            "config_hash": job.get("config_hash", ""),
            "baseline": result.get("baseline"),
            "actual": result.get("actual"),
            "delta": result.get("delta"),
            "threshold": spec.get("threshold"),
            "operator": spec.get("operator"),
            "metric": spec.get("metric"),
            "deadline_at": job.get("deadline_at"),
            "evaluated_at": _now_iso(),
            "failure_reason": result.get("failure_reason"),
            "trace_id": job.get("trace_id"),
            "attempts": job.get("attempts", 0),
        }

    def _log_decision(self, job: dict, payload: dict, outcome: str):
        self._decision_logger.log({
            "event": outcome,
            "job_id": job["job_id"],
            "action_id": job["action_id"],
            "decision_id": job["decision_id"],
            "config_hash": job.get("config_hash", ""),
            "outcome": outcome,
            "metric": payload.get("metric"),
            "baseline": payload.get("baseline"),
            "actual": payload.get("actual"),
            "delta": payload.get("delta"),
        })

    def _emit_calibration(self, job: dict, payload: dict, outcome: str):
        cal_id = _sha256(
            job.get("verify_spec_hash", ""),
            job.get("config_hash", ""),
            job.get("job_id", ""),
        )
        cal_record = {
            "calibration_record_id": cal_id,
            "job_id": job["job_id"],
            "decision_id": job["decision_id"],
            "action_id": job["action_id"],
            "action_type": job.get("action_type", ""),
            "outcome": outcome,
            "verify_spec_hash": job.get("verify_spec_hash", ""),
            "config_hash": job.get("config_hash", ""),
            "baseline": payload.get("baseline"),
            "actual": payload.get("actual"),
            "delta": payload.get("delta"),
            "threshold": payload.get("threshold"),
            "operator": payload.get("operator"),
            "evaluated_at": payload.get("evaluated_at"),
            "trace_id": job.get("trace_id"),
        }
        self._bus.publish("CALIBRATION_VERIFICATION_OUTCOME", cal_record)

    # ------------------------------------------------------------------
    # SwarmHealth heartbeat
    # ------------------------------------------------------------------

    def emit_heartbeat(self):
        """Publish a SwarmHealth heartbeat with queue metrics."""
        stats = self._jobs.stats()
        heartbeat = {
            "runner_id": self._runner_id,
            "time": _now_iso(),
            "pending": stats.get(STATUS_QUEUED, 0)
                       + stats.get(STATUS_WAITING, 0),
            "passed": self._metrics["passed"],
            "failed": self._metrics["failed"],
            "deadlettered": self._metrics["deadlettered"],
            "rollbacks": self._metrics["rollbacks"],
            "enqueued": self._metrics["enqueued"],
        }
        self._bus.publish("SWARM_HEALTH_HEARTBEAT", heartbeat)
        return heartbeat

    # ------------------------------------------------------------------
    # Async scheduler (Postgres mode)
    # ------------------------------------------------------------------

    async def run_async(self, pg_dsn: str | None = None):
        """Main event-driven loop for Postgres-backed mode.

        * Sleeps until the next deadline or a NOTIFY wakeup.
        * Claims due jobs via lease + SKIP LOCKED.
        * Evaluates and finalizes.
        """
        if not self._async_mode:
            raise RuntimeError("run_async requires pg_pool")

        try:
            import asyncpg
        except ImportError:
            raise RuntimeError("asyncpg is required for Postgres mode")

        pool = self._jobs._pool
        conn = await pool.acquire()
        await conn.add_listener("vr_jobs", self._pg_notify_cb)

        self._wakeup = asyncio.Event()
        print(f"[verify] async scheduler started (runner={self._runner_id})")

        try:
            while True:
                next_dl = await self._jobs.next_deadline()
                if next_dl:
                    wait_secs = max(
                        0, (next_dl - _now_utc()).total_seconds())
                else:
                    wait_secs = HEARTBEAT_INTERVAL_SECONDS

                # Sleep until deadline or wakeup
                self._wakeup.clear()
                try:
                    await asyncio.wait_for(
                        self._wakeup.wait(), timeout=wait_secs)
                except asyncio.TimeoutError:
                    pass

                # Claim and process due jobs
                claimed = await self._jobs.claim_due(
                    self._runner_id, self._lease_seconds)
                for job in claimed:
                    if job["attempts"] > self._max_attempts:
                        await self._async_dead_letter(job)
                    else:
                        await self._async_evaluate(job)

                # Periodic heartbeat
                self.emit_heartbeat()
        finally:
            await conn.remove_listener("vr_jobs", self._pg_notify_cb)
            await pool.release(conn)

    def _pg_notify_cb(self, conn, pid, channel, payload):
        """Callback for LISTEN/NOTIFY; wakes the scheduler."""
        if hasattr(self, "_wakeup"):
            self._wakeup.set()

    async def _async_evaluate(self, job: dict):
        result = self._evaluator.evaluate(job)
        passed = result["passed"]
        outcome_status = STATUS_PASSED if passed else STATUS_FAILED
        event_type = "VERIFY_PASSED" if passed else "VERIFY_FAILED"
        payload = self._build_outcome_payload(job, result, outcome_status)

        finalized = await self._jobs.finalize(
            str(job["job_id"]), self._runner_id,
            outcome_status, event_type,
            error=result.get("failure_reason"))
        if not finalized:
            return

        await self._jobs.append_outcome({
            "job_id": str(job["job_id"]),
            "decision_id": job["decision_id"],
            "action_id": job["action_id"],
            "status": outcome_status,
            "payload": payload,
        })

        self._bus.publish(event_type, payload)
        self._vstore.log(payload)
        self._log_decision(job, payload, outcome_status)
        self._emit_calibration(job, payload, outcome_status)

        if passed:
            self._metrics["passed"] += 1
        else:
            self._metrics["failed"] += 1
            self._do_rollback(job)

    async def _async_dead_letter(self, job: dict):
        reason = "max_attempts_exceeded"
        success = await self._jobs.dead_letter(
            str(job["job_id"]), self._runner_id, reason)
        if not success:
            return
        self._metrics["deadlettered"] += 1
        self._bus.publish("DEADLETTERED", {
            "job_id": str(job["job_id"]),
            "action_id": job["action_id"],
            "reason": reason,
        })

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def runner_id(self) -> str:
        return self._runner_id

    @property
    def metrics(self) -> dict[str, int]:
        return dict(self._metrics)


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Swarmz Verification Runner Service")
    parser.add_argument(
        "--pg-dsn", default=os.environ.get("VR_PG_DSN"),
        help="Postgres DSN (default: $VR_PG_DSN).  "
             "Omit for in-process mode.")
    parser.add_argument(
        "--loop", action="store_true",
        help="Run continuously (in-process mode)")
    parser.add_argument(
        "--interval", type=float, default=2.0,
        help="Check interval in seconds (in-process mode)")
    args = parser.parse_args()

    bus = EventDebouncer(window=0.5)
    store = StateStore()
    vstore = VerificationStore()
    adapter = SwarmzAdapter(store, bus)

    if args.pg_dsn:
        # Postgres-backed async mode
        import asyncio
        try:
            import asyncpg
        except ImportError:
            sys.exit("asyncpg is required for Postgres mode: "
                     "pip install asyncpg")

        async def _run():
            pool = await asyncpg.create_pool(args.pg_dsn)
            runner = VerificationRunner(
                store, vstore, bus, adapter, pg_pool=pool)
            await runner.run_async()

        print("[verify] starting Postgres-backed async scheduler")
        asyncio.run(_run())
    else:
        # In-process synchronous mode
        runner = VerificationRunner(store, vstore, bus, adapter)

        if args.loop:
            print("[verify] entering loop mode (Ctrl-C to stop)")
            try:
                while True:
                    runner.check_pending()
                    runner.emit_heartbeat()
                    time.sleep(args.interval)
            except KeyboardInterrupt:
                print("\n[verify] stopped")
        else:
            runner.check_pending()
            print("[verify] one-shot check complete")


if __name__ == "__main__":
    main()

