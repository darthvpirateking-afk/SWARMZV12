"""
core/governance_perf.py — Governance Pipeline Performance Monitor

Tracks per-layer latency and pass/block ratios for the NEXUSMON governance engine.

Usage:
    from core.governance_perf import perf_ledger, timed_layer

    with timed_layer("geometry"):
        result = geometry.evaluate(action, context)
    perf_ledger.record("geometry", elapsed_ms, passed=result.passed)

    summary = perf_ledger.summary()
"""

from __future__ import annotations

import time
import statistics
from collections import deque
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Dict, Optional


# How many recent samples to keep per layer (ring buffer)
_WINDOW = 200

# Alert threshold in milliseconds
SLOW_LAYER_THRESHOLD_MS = 50.0   # single layer
SLOW_PIPELINE_THRESHOLD_MS = 100.0  # full pipeline


@dataclass
class LayerPerf:
    """Rolling performance metrics for a single governance layer."""
    name: str
    latencies_ms: deque = field(default_factory=lambda: deque(maxlen=_WINDOW))
    pass_count: int = 0
    block_count: int = 0
    warn_count: int = 0
    total_calls: int = 0
    _last_alert: float = 0.0  # epoch of last slow-layer alert

    def record(self, elapsed_ms: float, passed: Optional[bool]) -> None:
        self.latencies_ms.append(elapsed_ms)
        self.total_calls += 1
        if passed is True:
            self.pass_count += 1
        elif passed is False:
            self.block_count += 1
        else:
            self.warn_count += 1

    def percentile(self, p: float) -> float:
        """Return the p-th percentile of recorded latencies (0–100)."""
        if not self.latencies_ms:
            return 0.0
        sorted_lats = sorted(self.latencies_ms)
        idx = max(0, int(len(sorted_lats) * p / 100) - 1)
        return sorted_lats[min(idx, len(sorted_lats) - 1)]

    @property
    def p50(self) -> float:
        return self.percentile(50)

    @property
    def p95(self) -> float:
        return self.percentile(95)

    @property
    def p99(self) -> float:
        return self.percentile(99)

    @property
    def mean(self) -> float:
        return statistics.mean(self.latencies_ms) if self.latencies_ms else 0.0

    @property
    def block_rate(self) -> float:
        if not self.total_calls:
            return 0.0
        return self.block_count / self.total_calls

    def to_dict(self) -> dict:
        return {
            "layer": self.name,
            "total_calls": self.total_calls,
            "pass": self.pass_count,
            "block": self.block_count,
            "warn": self.warn_count,
            "block_rate": round(self.block_rate, 4),
            "latency_ms": {
                "p50": round(self.p50, 3),
                "p95": round(self.p95, 3),
                "p99": round(self.p99, 3),
                "mean": round(self.mean, 3),
            },
            "sample_count": len(self.latencies_ms),
        }


class GovernancePerfLedger:
    """
    Central performance ledger for all 12 governance layers and the full pipeline.

    Thread-safety note: deque and int operations are GIL-protected in CPython.
    For multi-process use, replace with a shared-memory or Redis backend.
    """

    LAYER_ORDER = [
        "geometry",
        "integrity",
        "scoring",
        "threshold",
        "reversible",
        "sovereign",
        "shadow",
        "boundaries",
        "stabilization",
        "exploration",
        "emergence",
        "uplift",
        "_pipeline",  # total end-to-end
    ]

    def __init__(self) -> None:
        self._layers: Dict[str, LayerPerf] = {
            name: LayerPerf(name) for name in self.LAYER_ORDER
        }
        self._alerts: deque = deque(maxlen=100)  # recent slow-layer alerts

    def record(self, layer: str, elapsed_ms: float, passed: Optional[bool] = None) -> None:
        """Record a single layer evaluation result."""
        if layer not in self._layers:
            self._layers[layer] = LayerPerf(layer)
        lp = self._layers[layer]
        lp.record(elapsed_ms, passed)

        # Emit alert if layer is slow
        threshold = SLOW_PIPELINE_THRESHOLD_MS if layer == "_pipeline" else SLOW_LAYER_THRESHOLD_MS
        now = time.time()
        if elapsed_ms > threshold and (now - lp._last_alert) > 60:
            lp._last_alert = now
            self._alerts.append({
                "ts": now,
                "layer": layer,
                "elapsed_ms": round(elapsed_ms, 2),
                "threshold_ms": threshold,
                "msg": f"[GOVERNANCE PERF] {layer} took {elapsed_ms:.1f}ms (>{threshold}ms threshold)",
            })

    def summary(self) -> dict:
        """Return full performance summary suitable for the dashboard API."""
        layers_out = {}
        for name, lp in self._layers.items():
            if lp.total_calls > 0:
                layers_out[name] = lp.to_dict()

        pipeline = self._layers.get("_pipeline")
        return {
            "layers": layers_out,
            "pipeline": pipeline.to_dict() if pipeline and pipeline.total_calls else {},
            "alerts": list(self._alerts),
            "thresholds": {
                "slow_layer_ms": SLOW_LAYER_THRESHOLD_MS,
                "slow_pipeline_ms": SLOW_PIPELINE_THRESHOLD_MS,
            },
        }

    def reset(self) -> None:
        """Clear all samples (useful for tests)."""
        for lp in self._layers.values():
            lp.latencies_ms.clear()
            lp.pass_count = 0
            lp.block_count = 0
            lp.warn_count = 0
            lp.total_calls = 0
        self._alerts.clear()


# Module-level singleton
perf_ledger = GovernancePerfLedger()


@contextmanager
def timed_layer(layer_name: str, passed: Optional[bool] = None):
    """
    Context manager that measures layer execution time and records it.

    Usage:
        with timed_layer("geometry") as t:
            result = layer.evaluate(action, context)
        perf_ledger.record("geometry", t.elapsed_ms, result.passed)

    Or use the simpler auto-record form:
        with timed_layer("geometry", passed=None) as t:
            ...  # elapsed_ms available on t after exit
    """
    start = time.perf_counter()

    class _Timer:
        elapsed_ms: float = 0.0

    timer = _Timer()
    try:
        yield timer
    finally:
        timer.elapsed_ms = (time.perf_counter() - start) * 1000.0
        perf_ledger.record(layer_name, timer.elapsed_ms, passed)
