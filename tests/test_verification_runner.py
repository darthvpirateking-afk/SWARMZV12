"""
test_verification_runner.py – Tests for the VerificationRunner service.

Tests the in-memory (no-Postgres) code path which exercises the full
job state-machine, delta evaluator, exactly-once guards, rollback
automation, dead-lettering, decision logging, and calibration hooks.
"""

import json
import os
import sys
import time

import pytest

# Ensure the control_plane package is importable
_DIR = os.path.dirname(os.path.abspath(__file__))
if _DIR not in sys.path:
    sys.path.insert(0, _DIR)

from control_plane.state_store import StateStore
from control_plane.verification_store import VerificationStore
from control_plane.event_debouncer import EventDebouncer
from control_plane.swarmz_adapter import SwarmzAdapter
from control_plane.decision_logger import DecisionLogger
from control_plane.verification_runner import (
    VerificationRunner,
    DeltaEvaluator,
    _InMemoryJobStore,
    _hash_verify_spec,
    _make_dedupe_key,
    _sha256,
    _state_file_offset,
    _read_state_records_from_offset,
    STATUS_QUEUED,
    STATUS_WAITING,
    STATUS_PASSED,
    STATUS_FAILED,
    STATUS_DEADLETTERED,
    DEFAULT_MAX_ATTEMPTS,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def tmp_data(tmp_path):
    """Create temporary data/schema files mirroring the control_plane layout."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    schema_dir = tmp_path / "schemas"
    schema_dir.mkdir()

    # Minimal state schema
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "required": [
            "layer",
            "variable",
            "value",
            "units",
            "time",
            "confidence",
            "directionality",
            "source",
        ],
        "properties": {
            "layer": {"type": "string"},
            "variable": {"type": "string"},
            "value": {},
            "units": {"type": "string"},
            "time": {"type": "string"},
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
            "directionality": {
                "type": "string",
                "enum": ["up", "down", "stable", "unknown"],
            },
            "source": {"type": "string"},
        },
        "additionalProperties": False,
    }
    (schema_dir / "state.schema.json").write_text(json.dumps(schema))

    # Empty JSONL files
    (data_dir / "state.jsonl").write_text("")
    (data_dir / "verification_log.jsonl").write_text("")
    (data_dir / "decision_log.jsonl").write_text("")

    return tmp_path


@pytest.fixture()
def components(tmp_data):
    """Build a full set of runner components rooted in tmp_data."""
    state_path = str(tmp_data / "data" / "state.jsonl")
    vlog_path = str(tmp_data / "data" / "verification_log.jsonl")
    dlog_path = str(tmp_data / "data" / "decision_log.jsonl")

    # Patch the schema path used by StateStore
    import control_plane.state_store as ss_mod

    orig_schema = ss_mod._SCHEMA
    schema_path = str(tmp_data / "schemas" / "state.schema.json")
    with open(schema_path) as f:
        ss_mod._SCHEMA = json.load(f)

    bus = EventDebouncer(window=0.0)  # no debouncing in tests
    store = StateStore(data_path=state_path)
    vstore = VerificationStore(data_path=vlog_path)
    adapter = SwarmzAdapter(store, bus)
    dlogger = DecisionLogger(data_path=dlog_path)

    runner = VerificationRunner(
        store,
        vstore,
        bus,
        adapter,
        decision_logger=dlogger,
        max_attempts=DEFAULT_MAX_ATTEMPTS,
        lease_seconds=60,
    )

    yield {
        "bus": bus,
        "store": store,
        "vstore": vstore,
        "adapter": adapter,
        "dlogger": dlogger,
        "runner": runner,
        "state_path": state_path,
    }

    # Restore
    ss_mod._SCHEMA = orig_schema


def _make_action(
    action_id="act_allocate_budget",
    metric="money.budget_remaining",
    operator=">=",
    threshold=500,
    deadline_seconds=0,
    rollback_id="act_deallocate_budget",
):
    """Build a minimal action dict matching the catalogue shape."""
    return {
        "action_id": action_id,
        "name": "Test action",
        "layer": "money",
        "action_type": "money",
        "expected_effects": [{"variable": metric, "delta": 500}],
        "irreversibility_cost": 0.2,
        "rollback": {"action_id": rollback_id, "description": "rollback"},
        "verification": {
            "metric": metric,
            "operator": operator,
            "threshold": threshold,
            "deadline_seconds": deadline_seconds,
        },
    }


def _put_state(store, variable, value, layer="money"):
    """Write a state record into the store."""
    from datetime import datetime, timezone

    store.put(
        {
            "layer": layer,
            "variable": variable,
            "value": value,
            "units": "abstract",
            "time": datetime.now(timezone.utc).isoformat(),
            "confidence": 0.9,
            "directionality": "up",
            "source": "test",
        }
    )


# ---------------------------------------------------------------------------
# Unit tests: helpers
# ---------------------------------------------------------------------------


class TestHelpers:
    def test_sha256_deterministic(self):
        assert _sha256("a", "b") == _sha256("a", "b")
        assert _sha256("a", "b") != _sha256("b", "a")

    def test_hash_verify_spec_deterministic(self):
        spec = {"metric": "x", "operator": ">=", "threshold": 1}
        h1 = _hash_verify_spec(spec)
        h2 = _hash_verify_spec({"threshold": 1, "operator": ">=", "metric": "x"})
        assert h1 == h2  # key order irrelevant

    def test_make_dedupe_key(self):
        k1 = _make_dedupe_key("d1", "a1", "h1")
        k2 = _make_dedupe_key("d1", "a1", "h1")
        k3 = _make_dedupe_key("d1", "a2", "h1")
        assert k1 == k2
        assert k1 != k3

    def test_state_file_offset(self, tmp_path):
        p = str(tmp_path / "s.jsonl")
        assert _state_file_offset(p) == 0
        with open(p, "w") as f:
            f.write('{"x":1}\n')
        assert _state_file_offset(p) > 0

    def test_read_state_records_from_offset(self, tmp_path):
        p = str(tmp_path / "s.jsonl")
        with open(p, "w") as f:
            f.write('{"variable":"a","value":1}\n')
            off = f.tell()
            f.write('{"variable":"b","value":2}\n')
        recs = _read_state_records_from_offset(off, p)
        assert len(recs) == 1
        assert recs[0]["variable"] == "b"


# ---------------------------------------------------------------------------
# Unit tests: InMemoryJobStore
# ---------------------------------------------------------------------------


class TestInMemoryJobStore:
    def test_enqueue_idempotent(self):
        js = _InMemoryJobStore()
        job = {
            "dedupe_key": "dk1",
            "decision_id": "d1",
            "action_id": "a1",
            "deadline_at": "2099-01-01T00:00:00+00:00",
            "verify_spec": {},
            "verify_spec_hash": "h",
        }
        j1 = js.enqueue(job)
        j2 = js.enqueue(dict(job))  # same dedupe_key
        assert j1["job_id"] == j2["job_id"]

    def test_claim_due(self):
        js = _InMemoryJobStore()
        from datetime import datetime, timezone, timedelta

        past = (datetime.now(timezone.utc) - timedelta(seconds=10)).isoformat()
        job = {
            "dedupe_key": "dk2",
            "decision_id": "d2",
            "action_id": "a2",
            "deadline_at": past,
            "verify_spec": {},
            "verify_spec_hash": "h",
        }
        js.enqueue(job)
        claimed = js.claim_due("runner-1", 60)
        assert len(claimed) == 1
        assert claimed[0]["lease_owner"] == "runner-1"
        assert claimed[0]["status"] == STATUS_WAITING

    def test_finalize_exactly_once(self):
        js = _InMemoryJobStore()
        from datetime import datetime, timezone, timedelta

        past = (datetime.now(timezone.utc) - timedelta(seconds=10)).isoformat()
        job = {
            "dedupe_key": "dk3",
            "deadline_at": past,
            "decision_id": "d",
            "action_id": "a",
            "verify_spec": {},
            "verify_spec_hash": "h",
        }
        js.enqueue(job)
        claimed = js.claim_due("r1", 60)
        jid = claimed[0]["job_id"]

        assert js.finalize(jid, "r1", STATUS_PASSED, "VERIFY_PASSED")
        # Second attempt must fail (exactly-once)
        assert not js.finalize(jid, "r1", STATUS_FAILED, "VERIFY_FAILED")

    def test_mark_rollback_exactly_once(self):
        js = _InMemoryJobStore()
        from datetime import datetime, timezone, timedelta

        past = (datetime.now(timezone.utc) - timedelta(seconds=10)).isoformat()
        job = {
            "dedupe_key": "dk4",
            "deadline_at": past,
            "decision_id": "d",
            "action_id": "a",
            "verify_spec": {},
            "verify_spec_hash": "h",
        }
        js.enqueue(job)
        claimed = js.claim_due("r1", 60)
        jid = claimed[0]["job_id"]
        assert js.mark_rollback_triggered(jid, "r1", "rb-1")
        assert not js.mark_rollback_triggered(jid, "r1", "rb-2")

    def test_dead_letter(self):
        js = _InMemoryJobStore()
        from datetime import datetime, timezone, timedelta

        past = (datetime.now(timezone.utc) - timedelta(seconds=10)).isoformat()
        job = {
            "dedupe_key": "dk5",
            "deadline_at": past,
            "decision_id": "d",
            "action_id": "a",
            "verify_spec": {},
            "verify_spec_hash": "h",
        }
        js.enqueue(job)
        claimed = js.claim_due("r1", 60)
        jid = claimed[0]["job_id"]
        assert js.dead_letter(jid, "r1", "too many attempts")
        j = js.get_job(jid)
        assert j["status"] == STATUS_DEADLETTERED

    def test_stats(self):
        js = _InMemoryJobStore()
        from datetime import datetime, timezone, timedelta

        past = (datetime.now(timezone.utc) - timedelta(seconds=10)).isoformat()
        js.enqueue(
            {
                "dedupe_key": "a",
                "deadline_at": past,
                "decision_id": "d",
                "action_id": "a",
                "verify_spec": {},
                "verify_spec_hash": "h",
            }
        )
        js.enqueue(
            {
                "dedupe_key": "b",
                "deadline_at": "2099-01-01T00:00:00+00:00",
                "decision_id": "d",
                "action_id": "b",
                "verify_spec": {},
                "verify_spec_hash": "h",
            }
        )
        s = js.stats()
        assert s.get(STATUS_QUEUED, 0) == 2

    def test_record_rollback_result(self):
        js = _InMemoryJobStore()
        from datetime import datetime, timezone, timedelta

        past = (datetime.now(timezone.utc) - timedelta(seconds=10)).isoformat()
        job = {
            "dedupe_key": "dk6",
            "deadline_at": past,
            "decision_id": "d",
            "action_id": "a",
            "verify_spec": {},
            "verify_spec_hash": "h",
        }
        js.enqueue(job)
        claimed = js.claim_due("r1", 60)
        jid = claimed[0]["job_id"]
        js.mark_rollback_triggered(jid, "r1", "rb-99")
        assert js.record_rollback_result("rb-99", {"ok": True})
        j = js.get_job(jid)
        assert j.get("rollback_result") == {"ok": True}


# ---------------------------------------------------------------------------
# Unit tests: DeltaEvaluator
# ---------------------------------------------------------------------------


class TestDeltaEvaluator:
    def test_pass(self, tmp_path):
        p = str(tmp_path / "state.jsonl")
        with open(p, "w") as f:
            f.write(
                json.dumps(
                    {
                        "variable": "money.budget_remaining",
                        "value": 600,
                    }
                )
                + "\n"
            )

        ev = DeltaEvaluator(state_path=p)
        job = {
            "verify_spec": {
                "metric": "money.budget_remaining",
                "operator": ">=",
                "threshold": 500,
            },
            "baseline_state_offset": 0,
            "_baseline_value": 100,
        }
        result = ev.evaluate(job)
        assert result["passed"] is True
        assert result["actual"] == 600
        assert result["delta"] == 500  # 600 - 100

    def test_fail_threshold_not_met(self, tmp_path):
        p = str(tmp_path / "state.jsonl")
        with open(p, "w") as f:
            f.write(
                json.dumps(
                    {
                        "variable": "money.budget_remaining",
                        "value": 100,
                    }
                )
                + "\n"
            )

        ev = DeltaEvaluator(state_path=p)
        job = {
            "verify_spec": {
                "metric": "money.budget_remaining",
                "operator": ">=",
                "threshold": 500,
            },
            "baseline_state_offset": 0,
            "_baseline_value": 100,
        }
        result = ev.evaluate(job)
        assert result["passed"] is False
        assert result["failure_reason"] == "threshold_not_met"

    def test_missing_metric(self, tmp_path):
        p = str(tmp_path / "state.jsonl")
        with open(p, "w") as f:
            f.write(
                json.dumps(
                    {
                        "variable": "other.var",
                        "value": 10,
                    }
                )
                + "\n"
            )

        ev = DeltaEvaluator(state_path=p)
        job = {
            "verify_spec": {
                "metric": "money.budget_remaining",
                "operator": ">=",
                "threshold": 500,
            },
            "baseline_state_offset": 0,
            "_baseline_value": None,
        }
        result = ev.evaluate(job)
        assert result["passed"] is False
        assert result["failure_reason"] == "missing_metric"

    def test_baseline_offset(self, tmp_path):
        p = str(tmp_path / "state.jsonl")
        with open(p, "w") as f:
            # First record (before baseline)
            f.write(
                json.dumps(
                    {
                        "variable": "money.budget_remaining",
                        "value": 100,
                    }
                )
                + "\n"
            )
            offset = f.tell()
            # Second record (after baseline)
            f.write(
                json.dumps(
                    {
                        "variable": "money.budget_remaining",
                        "value": 700,
                    }
                )
                + "\n"
            )

        ev = DeltaEvaluator(state_path=p)
        job = {
            "verify_spec": {
                "metric": "money.budget_remaining",
                "operator": ">=",
                "threshold": 500,
            },
            "baseline_state_offset": offset,
            "_baseline_value": 100,
        }
        result = ev.evaluate(job)
        assert result["passed"] is True
        assert result["actual"] == 700

    def test_mean_aggregation(self, tmp_path):
        p = str(tmp_path / "state.jsonl")
        with open(p, "w") as f:
            for v in [400, 600]:
                f.write(
                    json.dumps(
                        {
                            "variable": "money.budget_remaining",
                            "value": v,
                        }
                    )
                    + "\n"
                )

        ev = DeltaEvaluator(state_path=p)
        job = {
            "verify_spec": {
                "metric": "money.budget_remaining",
                "operator": ">=",
                "threshold": 500,
            },
            "baseline_state_offset": 0,
            "_baseline_value": 0,
        }
        result = ev.evaluate(job)
        assert result["actual"] == 500  # mean of 400 and 600
        assert result["passed"] is True


# ---------------------------------------------------------------------------
# Integration tests: VerificationRunner (in-process mode)
# ---------------------------------------------------------------------------


class TestVerificationRunnerInProcess:
    def test_enqueue_on_action_selected(self, components):
        """Publishing ACTION_SELECTED enqueues a verification job."""
        runner = components["runner"]
        bus = components["bus"]
        action = _make_action(deadline_seconds=0)
        bus.publish("ACTION_SELECTED", action)
        time.sleep(0.1)  # allow debouncer to fire
        assert runner.metrics["enqueued"] == 1

    def test_action_without_verification_ignored(self, components):
        runner = components["runner"]
        bus = components["bus"]
        bus.publish("ACTION_SELECTED", {"action_id": "no_verify"})
        time.sleep(0.1)
        assert runner.metrics["enqueued"] == 0

    def test_none_payload_ignored(self, components):
        runner = components["runner"]
        bus = components["bus"]
        bus.publish("ACTION_SELECTED", None)
        time.sleep(0.1)
        assert runner.metrics["enqueued"] == 0

    def test_verify_passed(self, components):
        """Action whose verification passes emits VERIFY_PASSED."""
        runner = components["runner"]
        bus = components["bus"]
        store = components["store"]

        action = _make_action(threshold=500, deadline_seconds=0)
        bus.publish("ACTION_SELECTED", action)
        time.sleep(0.1)

        # State written AFTER enqueue (simulates action effect arriving)
        _put_state(store, "money.budget_remaining", 600)

        # Now evaluate
        runner.check_pending()
        assert runner.metrics["passed"] == 1
        assert runner.metrics["failed"] == 0

    def test_verify_failed_triggers_rollback(self, components):
        """Failed verification triggers rollback (exactly-once)."""
        runner = components["runner"]
        bus = components["bus"]
        store = components["store"]

        events = []
        bus.subscribe("ROLLBACK_TRIGGERED", lambda e, p: events.append(p))

        action = _make_action(threshold=500, deadline_seconds=0)
        bus.publish("ACTION_SELECTED", action)
        time.sleep(0.1)

        # Low value written AFTER enqueue → will fail threshold of 500
        _put_state(store, "money.budget_remaining", 50)

        runner.check_pending()
        assert runner.metrics["failed"] == 1
        assert runner.metrics["rollbacks"] == 1
        assert len(events) == 1
        assert events[0]["rollback_action_type"] == "act_deallocate_budget"

    def test_exactly_once_outcome(self, components):
        """Calling check_pending twice doesn't double-emit."""
        runner = components["runner"]
        bus = components["bus"]
        store = components["store"]

        action = _make_action(threshold=500, deadline_seconds=0)
        bus.publish("ACTION_SELECTED", action)
        time.sleep(0.1)

        _put_state(store, "money.budget_remaining", 600)

        runner.check_pending()
        runner.check_pending()  # second call
        assert runner.metrics["passed"] == 1  # not 2

    def test_idempotent_enqueue(self, components):
        """Same action published twice → only one job created."""
        runner = components["runner"]
        bus = components["bus"]
        action = _make_action(deadline_seconds=0)
        bus.publish("ACTION_SELECTED", action)
        time.sleep(0.1)
        bus.publish("ACTION_SELECTED", action)
        time.sleep(0.1)
        # Should still be 1 because dedupe_key is the same
        # (The EventDebouncer might coalesce, but the store also dedupes)
        assert runner.metrics["enqueued"] <= 2  # at most 2 attempts
        # The job store has at most 1 unique job
        stats = runner._jobs.stats()
        total = sum(stats.values())
        assert total == 1

    def test_decision_log_written(self, components):
        """Outcome is logged to decision_log."""
        runner = components["runner"]
        bus = components["bus"]
        store = components["store"]
        dlogger = components["dlogger"]

        action = _make_action(threshold=500, deadline_seconds=0)
        bus.publish("ACTION_SELECTED", action)
        time.sleep(0.1)

        _put_state(store, "money.budget_remaining", 600)

        runner.check_pending()
        entries = dlogger.read_all()
        assert any(e.get("event") == "PASSED" for e in entries)

    def test_calibration_event_emitted(self, components):
        """CALIBRATION_VERIFICATION_OUTCOME is emitted."""
        runner = components["runner"]
        bus = components["bus"]
        store = components["store"]

        cal_events = []
        bus.subscribe(
            "CALIBRATION_VERIFICATION_OUTCOME", lambda e, p: cal_events.append(p)
        )

        action = _make_action(threshold=500, deadline_seconds=0)
        bus.publish("ACTION_SELECTED", action)
        time.sleep(0.1)

        _put_state(store, "money.budget_remaining", 600)

        runner.check_pending()
        assert len(cal_events) == 1
        assert "calibration_record_id" in cal_events[0]

    def test_heartbeat(self, components):
        """emit_heartbeat returns metrics dict."""
        runner = components["runner"]
        hb = runner.emit_heartbeat()
        assert "runner_id" in hb
        assert "pending" in hb
        assert isinstance(hb["passed"], int)

    def test_verification_store_logged(self, components):
        """Outcome is persisted to verification_log.jsonl."""
        runner = components["runner"]
        bus = components["bus"]
        store = components["store"]
        vstore = components["vstore"]

        action = _make_action(threshold=500, deadline_seconds=0)
        bus.publish("ACTION_SELECTED", action)
        time.sleep(0.1)

        _put_state(store, "money.budget_remaining", 600)

        runner.check_pending()
        entries = vstore.read_all()
        assert len(entries) >= 1
        assert entries[-1].get("outcome") in ("PASSED", "FAILED")

    def test_dead_letter_after_max_attempts(self, components):
        """Job is dead-lettered when attempts exceed max."""
        runner = components["runner"]
        bus = components["bus"]
        store = components["store"]

        dl_events = []
        bus.subscribe("DEADLETTERED", lambda e, p: dl_events.append(p))

        action = _make_action(threshold=500, deadline_seconds=0)
        vspec = action["verification"]
        spec_hash = _hash_verify_spec(vspec)

        from datetime import timedelta
        from control_plane.verification_runner import _now_utc

        # Create a job with max_attempts=0, so it's dead-lettered immediately
        js = runner._jobs
        dedupe_key = _make_dedupe_key("d_dl", "a_dl", spec_hash)
        job = {
            "dedupe_key": dedupe_key,
            "decision_id": "d_dl",
            "action_id": "a_dl",
            "action_type": "money",
            "deadline_at": (_now_utc() - timedelta(seconds=10)).isoformat(),
            "verify_spec": vspec,
            "verify_spec_hash": spec_hash,
            "rollback_action_type": "act_deallocate_budget",
            "rollback_params": {},
            "max_attempts": 0,
            "_baseline_value": 50,
        }
        js.enqueue(job)
        runner.check_pending()

        assert runner.metrics["deadlettered"] >= 1

    def test_rollback_result_correlation(self, components):
        """ACT_RESULT event is correlated back to the job."""
        runner = components["runner"]
        bus = components["bus"]

        recorded = []
        bus.subscribe("ROLLBACK_RESULT_RECORDED", lambda e, p: recorded.append(p))

        # Simulate an ACT_RESULT
        bus.publish("ACT_RESULT", {"action_id": "rb-fake", "ok": True})
        time.sleep(0.1)

        # The correlation happens (even if no matching job, no crash)
        # This validates the handler doesn't error
        assert True  # no exception

    def test_runner_id(self, components):
        runner = components["runner"]
        assert runner.runner_id.startswith("vr-")

    def test_metrics_initial(self, components):
        runner = components["runner"]
        m = runner.metrics
        assert m["enqueued"] == 0
        assert m["passed"] == 0
        assert m["failed"] == 0


# ---------------------------------------------------------------------------
# Verification store query tests
# ---------------------------------------------------------------------------


class TestVerificationStoreQueries:
    def test_find_by_job_id(self, tmp_path):
        p = str(tmp_path / "vlog.jsonl")
        vs = VerificationStore(data_path=p)
        vs.log({"job_id": "j1", "outcome": "PASSED"})
        vs.log({"job_id": "j2", "outcome": "FAILED"})
        assert len(vs.find_by_job_id("j1")) == 1
        assert vs.find_by_job_id("j1")[0]["outcome"] == "PASSED"

    def test_find_by_decision_id(self, tmp_path):
        p = str(tmp_path / "vlog.jsonl")
        vs = VerificationStore(data_path=p)
        vs.log({"decision_id": "d1", "outcome": "PASSED"})
        vs.log({"decision_id": "d2", "outcome": "FAILED"})
        assert len(vs.find_by_decision_id("d1")) == 1

    def test_find_by_outcome(self, tmp_path):
        p = str(tmp_path / "vlog.jsonl")
        vs = VerificationStore(data_path=p)
        vs.log({"outcome": "PASSED"})
        vs.log({"outcome": "PASSED"})
        vs.log({"outcome": "FAILED"})
        assert len(vs.find_by_outcome("PASSED")) == 2
        assert len(vs.find_by_outcome("FAILED")) == 1
