"""
Stabilization Layer (P2.3 - Equilibrium Maintenance)

Dampens oscillations and maintains system equilibrium.
Prevents rapid state fluctuations and ensures smooth operation.

Design:
- Detect oscillating metrics
- Apply damping to rapid changes
- Enforce cooldown periods
- Maintain stability buffers
"""

import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Deque
from dataclasses import dataclass
from collections import deque

_CONFIG_DIR = Path(__file__).parent.parent / "config"
_STABILIZATION_CONFIG_FILE = _CONFIG_DIR / "governance" / "stabilization.json"

from core.reversible import LayerResult


@dataclass
class OscillationDetector:
    """Detects oscillating behavior in a metric."""

    metric_name: str
    window_size: int = 10
    threshold_crossings: int = 3  # Min crossings to detect oscillation
    values: Deque[float] = None

    def __post_init__(self):
        if self.values is None:
            self.values = deque(maxlen=self.window_size)

    def add_value(self, value: float):
        """Add a new value to the history."""
        self.values.append(value)

    def detect_oscillation(self) -> bool:
        """Check if metric is oscillating (crossing mean frequently)."""
        if len(self.values) < self.window_size:
            return False

        # Calculate mean
        mean = sum(self.values) / len(self.values)

        # Count threshold crossings
        crossings = 0
        prev_above = None

        for val in self.values:
            current_above = val > mean
            if prev_above is not None and current_above != prev_above:
                crossings += 1
            prev_above = current_above

        return crossings >= self.threshold_crossings


@dataclass
class CooldownTracker:
    """Tracks cooldown periods to prevent rapid changes."""

    action_type: str
    last_execution: float = 0.0
    cooldown_seconds: float = 60.0

    def is_ready(self) -> bool:
        """Check if cooldown period has elapsed."""
        return (time.time() - self.last_execution) >= self.cooldown_seconds

    def record_execution(self):
        """Record that action was executed."""
        self.last_execution = time.time()

    def remaining_cooldown(self) -> float:
        """Get remaining cooldown time in seconds."""
        elapsed = time.time() - self.last_execution
        remaining = self.cooldown_seconds - elapsed
        return max(0.0, remaining)


class StabilizationLayer:
    """
    System stability enforcement engine.

    Prevents rapid oscillations and enforces equilibrium.
    """

    def __init__(self, config_path: Optional[Path] = None):
        self.oscillation_detectors: Dict[str, OscillationDetector] = {}
        self.cooldown_trackers: Dict[str, CooldownTracker] = {}
        self.stability_buffer = 0.1  # 10% buffer to prevent flapping
        self._config_path = config_path or _STABILIZATION_CONFIG_FILE
        self._load_config()

    def _load_config(self) -> None:
        """Load cooldown and oscillation parameters from config file if present."""
        if not self._config_path.exists():
            return
        try:
            with open(self._config_path, "r") as f:
                cfg = json.load(f)
            # Apply oscillation detection settings
            osc = cfg.get("oscillation_detection", {})
            self._default_window_size = osc.get("window_size", 10)
            self._default_threshold_crossings = osc.get(
                "threshold_crossings_to_flag", 3
            )
            # Apply hysteresis buffer
            hyst = cfg.get("hysteresis", {})
            self.stability_buffer = hyst.get("default_buffer", 0.1)
            # Register configured cooldowns (opt-in)
            for action_type, seconds in cfg.get("cooldowns", {}).items():
                if not action_type.startswith("_"):
                    self.set_cooldown(action_type, float(seconds))
        except Exception:
            pass  # Config errors are non-fatal

    def track_metric(self, metric_name: str, value: float):
        """Add a metric value to oscillation tracking."""
        if metric_name not in self.oscillation_detectors:
            self.oscillation_detectors[metric_name] = OscillationDetector(metric_name)

        self.oscillation_detectors[metric_name].add_value(value)

    def is_oscillating(self, metric_name: str) -> bool:
        """Check if a metric is oscillating."""
        detector = self.oscillation_detectors.get(metric_name)
        if detector is None:
            return False
        return detector.detect_oscillation()

    def set_cooldown(self, action_type: str, cooldown_seconds: float):
        """Configure cooldown for an action type."""
        if action_type not in self.cooldown_trackers:
            self.cooldown_trackers[action_type] = CooldownTracker(action_type)

        self.cooldown_trackers[action_type].cooldown_seconds = cooldown_seconds

    def check_cooldown(self, action_type: str) -> tuple[bool, float]:
        """
        Check if action is ready (cooldown elapsed).

        Returns (is_ready, remaining_cooldown).
        """
        tracker = self.cooldown_trackers.get(action_type)
        if tracker is None:
            # No cooldown configured = always ready
            return True, 0.0

        return tracker.is_ready(), tracker.remaining_cooldown()

    def record_action(self, action_type: str):
        """Record that an action was executed (start cooldown)."""
        if action_type not in self.cooldown_trackers:
            self.cooldown_trackers[action_type] = CooldownTracker(action_type)

        self.cooldown_trackers[action_type].record_execution()

    def apply_damping(
        self, current_value: float, target_value: float, damping_factor: float = 0.5
    ) -> float:
        """
        Apply damping to smooth rapid changes.

        Args:
            current_value: Current state
            target_value: Desired target
            damping_factor: 0-1, higher = more damping (slower change)

        Returns:
            Damped value between current and target
        """
        change = target_value - current_value
        damped_change = change * (1.0 - damping_factor)
        return current_value + damped_change

    def apply_hysteresis(
        self, value: float, threshold: float, last_state: bool
    ) -> bool:
        """
        Apply hysteresis to prevent threshold flapping.

        Args:
            value: Current value
            threshold: Decision threshold
            last_state: Previous boolean state

        Returns:
            New state with stability buffer applied
        """
        buffer = threshold * self.stability_buffer

        if last_state:
            # Currently True, require drop below threshold - buffer to flip
            return value >= (threshold - buffer)
        else:
            # Currently False, require rise above threshold + buffer to flip
            return value >= (threshold + buffer)

    def evaluate(self, action: Dict[str, Any], context: Dict[str, Any]) -> LayerResult:
        """
        Entry point for pipeline composition.

        Checks for oscillations and enforces cooldowns.
        """
        action_type = action.get("action_type", "unknown")

        # Track metrics for oscillation detection
        for key, value in context.items():
            if isinstance(value, (int, float)):
                self.track_metric(key, float(value))

        # Check for oscillations
        oscillating_metrics = [
            name
            for name, detector in self.oscillation_detectors.items()
            if detector.detect_oscillation()
        ]

        # Check cooldown
        is_ready, remaining = self.check_cooldown(action_type)

        if not is_ready:
            return LayerResult(
                layer="stabilization",
                passed=False,
                reason=f"Action in cooldown: {remaining:.1f}s remaining",
                metadata={
                    "action_type": action_type,
                    "cooldown_remaining": remaining,
                },
                timestamp=time.time(),
            )

        # Check for system instability
        if oscillating_metrics:
            return LayerResult(
                layer="stabilization",
                passed=False,
                reason=f"System oscillating: {', '.join(oscillating_metrics)}",
                metadata={
                    "oscillating_metrics": oscillating_metrics,
                    "action_blocked": True,
                },
                timestamp=time.time(),
            )

        # Record action execution only if cooldown is configured
        if action_type in self.cooldown_trackers:
            self.record_action(action_type)

        return LayerResult(
            layer="stabilization",
            passed=True,
            reason="System stable, cooldown OK",
            metadata={
                "action_type": action_type,
                "tracked_metrics": len(self.oscillation_detectors),
            },
            timestamp=time.time(),
        )

    def get_oscillating_metrics(self) -> List[str]:
        """Get list of currently oscillating metrics."""
        return [
            name
            for name, detector in self.oscillation_detectors.items()
            if detector.detect_oscillation()
        ]


# Module-level instance
_stabilization = StabilizationLayer()


def track_metric(metric_name: str, value: float):
    """Track metric using global instance."""
    _stabilization.track_metric(metric_name, value)


def is_oscillating(metric_name: str) -> bool:
    """Check oscillation using global instance."""
    return _stabilization.is_oscillating(metric_name)


def set_cooldown(action_type: str, cooldown_seconds: float):
    """Set cooldown using global instance."""
    _stabilization.set_cooldown(action_type, cooldown_seconds)


def check_cooldown(action_type: str) -> tuple[bool, float]:
    """Check cooldown using global instance."""
    return _stabilization.check_cooldown(action_type)


def apply_damping(
    current_value: float, target_value: float, damping_factor: float = 0.5
) -> float:
    """Apply damping using global instance."""
    return _stabilization.apply_damping(current_value, target_value, damping_factor)


def evaluate(action: Dict[str, Any], context: Dict[str, Any]) -> LayerResult:
    """Standalone evaluation."""
    return _stabilization.evaluate(action, context)
