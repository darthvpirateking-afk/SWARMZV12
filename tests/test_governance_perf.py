"""
tests/test_governance_perf.py — Tests for governance performance monitoring.
"""

import time
import pytest
from core.governance_perf import (
    GovernancePerfLedger,
    LayerPerf,
    perf_ledger,
    timed_layer,
    SLOW_LAYER_THRESHOLD_MS,
    SLOW_PIPELINE_THRESHOLD_MS,
)


@pytest.fixture
def fresh_ledger():
    ledger = GovernancePerfLedger()
    return ledger


# ── LayerPerf unit tests ──────────────────────────────────────────────────────

def test_layer_perf_records_pass(fresh_ledger):
    fresh_ledger.record("geometry", 1.5, True)
    lp = fresh_ledger._layers["geometry"]
    assert lp.pass_count == 1
    assert lp.block_count == 0
    assert lp.total_calls == 1


def test_layer_perf_records_block(fresh_ledger):
    fresh_ledger.record("integrity", 2.0, False)
    lp = fresh_ledger._layers["integrity"]
    assert lp.block_count == 1
    assert lp.pass_count == 0


def test_layer_perf_records_unknown_passed(fresh_ledger):
    fresh_ledger.record("emergence", 0.5, None)
    lp = fresh_ledger._layers["emergence"]
    assert lp.warn_count == 1
    assert lp.pass_count == 0
    assert lp.block_count == 0


def test_block_rate_calculation(fresh_ledger):
    for _ in range(8):
        fresh_ledger.record("scoring", 1.0, True)
    for _ in range(2):
        fresh_ledger.record("scoring", 1.0, False)
    lp = fresh_ledger._layers["scoring"]
    assert abs(lp.block_rate - 0.2) < 0.001


def test_percentile_p50(fresh_ledger):
    for ms in [1.0, 2.0, 3.0, 4.0, 5.0]:
        fresh_ledger.record("threshold", ms, True)
    lp = fresh_ledger._layers["threshold"]
    p50 = lp.p50
    assert 2.0 <= p50 <= 4.0  # rough middle


def test_percentile_p99_with_outlier(fresh_ledger):
    # 98 normal + 2 slow → p99 (sorted[98]) = first slow item
    for _ in range(98):
        fresh_ledger.record("boundaries", 1.0, True)
    for _ in range(2):
        fresh_ledger.record("boundaries", 500.0, True)
    lp = fresh_ledger._layers["boundaries"]
    assert lp.p99 >= 100.0
    assert lp.p50 < 10.0


def test_mean_latency(fresh_ledger):
    for ms in [10.0, 20.0, 30.0]:
        fresh_ledger.record("stabilization", ms, True)
    lp = fresh_ledger._layers["stabilization"]
    assert abs(lp.mean - 20.0) < 0.01


def test_to_dict_structure(fresh_ledger):
    fresh_ledger.record("exploration", 5.0, True)
    lp = fresh_ledger._layers["exploration"]
    d = lp.to_dict()
    assert "total_calls" in d
    assert "latency_ms" in d
    assert set(d["latency_ms"].keys()) == {"p50", "p95", "p99", "mean"}
    assert "block_rate" in d


# ── GovernancePerfLedger tests ────────────────────────────────────────────────

def test_summary_includes_recorded_layers(fresh_ledger):
    fresh_ledger.record("geometry", 1.0, True)
    fresh_ledger.record("integrity", 2.0, True)
    summary = fresh_ledger.summary()
    assert "geometry" in summary["layers"]
    assert "integrity" in summary["layers"]


def test_summary_excludes_empty_layers(fresh_ledger):
    fresh_ledger.record("geometry", 1.0, True)
    summary = fresh_ledger.summary()
    # integrity never recorded — should not appear
    assert "integrity" not in summary["layers"]


def test_alert_fires_for_slow_layer(fresh_ledger):
    fresh_ledger.record("geometry", SLOW_LAYER_THRESHOLD_MS + 10.0, True)
    assert len(fresh_ledger._alerts) == 1
    alert = fresh_ledger._alerts[0]
    assert alert["layer"] == "geometry"
    assert "GOVERNANCE PERF" in alert["msg"]


def test_alert_fires_for_slow_pipeline(fresh_ledger):
    fresh_ledger.record("_pipeline", SLOW_PIPELINE_THRESHOLD_MS + 50.0, True)
    assert len(fresh_ledger._alerts) == 1
    alert = fresh_ledger._alerts[0]
    assert alert["layer"] == "_pipeline"


def test_no_alert_under_threshold(fresh_ledger):
    fresh_ledger.record("geometry", SLOW_LAYER_THRESHOLD_MS - 1.0, True)
    assert len(fresh_ledger._alerts) == 0


def test_reset_clears_data(fresh_ledger):
    fresh_ledger.record("geometry", 10.0, True)
    fresh_ledger.reset()
    assert fresh_ledger._layers["geometry"].total_calls == 0
    assert len(fresh_ledger._alerts) == 0


def test_unknown_layer_auto_created(fresh_ledger):
    fresh_ledger.record("custom_layer", 3.0, True)
    assert "custom_layer" in fresh_ledger._layers


# ── timed_layer context manager tests ────────────────────────────────────────

def test_timed_layer_records_elapsed(fresh_ledger):
    # Temporarily swap module-level ledger via monkeypatching
    import core.governance_perf as gp
    orig = gp.perf_ledger
    gp.perf_ledger = fresh_ledger
    try:
        with timed_layer("geometry") as t:
            time.sleep(0.01)  # 10ms
        assert t.elapsed_ms >= 5.0
        assert fresh_ledger._layers["geometry"].total_calls == 1
    finally:
        gp.perf_ledger = orig


# ── Integration: perf_ledger wired into tool_gate ────────────────────────────

def test_gate_call_populates_perf_ledger():
    """After gate(), perf_ledger should have entries for at least geometry."""
    from core.tool_gate import gate
    perf_ledger.reset()
    gate("command", {"cmd": "echo hello"})
    summary = perf_ledger.summary()
    # At least geometry should be recorded
    assert "geometry" in summary["layers"] or summary["pipeline"]
