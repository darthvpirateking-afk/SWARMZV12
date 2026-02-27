"""
Emergence Layer (P2.1 - Pattern Detection)

Detects emergent patterns and behaviors in system execution.
Tracks unexpected interactions and self-organizing behavior.

Design:
- Pattern matching on execution history
- Anomaly detection for emergent behavior
- Correlation analysis across actions
- Deterministic pattern recognition (no ML randomness)
"""

import time
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict, deque

from core.reversible import LayerResult


@dataclass
class Pattern:
    """A detected emergent pattern."""

    pattern_id: str
    pattern_type: str  # "sequence", "correlation", "anomaly", "cycle"
    frequency: int
    first_seen: float
    last_seen: float
    confidence: float  # 0-1
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EmergenceEvent:
    """Records a detected emergence event."""

    timestamp: float
    event_type: str
    description: str
    patterns_involved: List[str]
    strength: float  # 0-1 how strong the emergence signal


class EmergenceLayer:
    """
    Pattern detection engine for emergent behavior.

    Analyzes execution history to identify:
    - Repeated sequences
    - Correlations between actions
    - Anomalous behavior
    - Cyclic patterns
    """

    def __init__(self, history_size: int = 1000):
        self.history_size = history_size
        self.action_history: deque = deque(maxlen=history_size)
        self.patterns: Dict[str, Pattern] = {}
        self.emergence_events: List[EmergenceEvent] = []
        self._pattern_counter = 0

    def record_action(self, action: Dict[str, Any], context: Dict[str, Any]):
        """Add action to history for pattern analysis."""
        self.action_history.append(
            {
                "timestamp": time.time(),
                "action": action,
                "context": context,
            }
        )

    def detect_sequence_pattern(
        self, sequence_length: int = 3, min_occurrences: int = 2
    ) -> List[Pattern]:
        """
        Detect repeated action sequences.

        Example: A -> B -> C appearing multiple times suggests emergent workflow.
        """
        if len(self.action_history) < sequence_length:
            return []

        # Extract action types
        action_types = [
            entry["action"].get("action_type", "unknown")
            for entry in self.action_history
        ]

        # Count sequences
        sequence_counts = defaultdict(int)
        for i in range(len(action_types) - sequence_length + 1):
            seq = tuple(action_types[i : i + sequence_length])
            sequence_counts[seq] += 1

        # Identify patterns
        patterns = []
        for seq, count in sequence_counts.items():
            if count >= min_occurrences:
                pattern_id = f"seq_{self._pattern_counter}"
                self._pattern_counter += 1

                # Find first/last occurrence
                first_seen = None
                last_seen = None
                for i in range(len(action_types) - sequence_length + 1):
                    if tuple(action_types[i : i + sequence_length]) == seq:
                        timestamp = self.action_history[i]["timestamp"]
                        if first_seen is None:
                            first_seen = timestamp
                        last_seen = timestamp

                pattern = Pattern(
                    pattern_id=pattern_id,
                    pattern_type="sequence",
                    frequency=count,
                    first_seen=first_seen or time.time(),
                    last_seen=last_seen or time.time(),
                    confidence=min(
                        count / 10.0, 1.0
                    ),  # More occurrences = higher confidence
                    metadata={"sequence": seq, "length": sequence_length},
                )
                patterns.append(pattern)
                self.patterns[pattern_id] = pattern

        return patterns

    def detect_correlation(
        self, field_a: str, field_b: str, threshold: float = 0.7
    ) -> Optional[Pattern]:
        """
        Detect correlation between two context fields.

        Example: high budget_remaining correlates with low risk_score.
        """
        if len(self.action_history) < 10:
            return None

        # Extract field values
        values_a = []
        values_b = []

        for entry in self.action_history:
            ctx = entry["context"]
            val_a = ctx.get(field_a)
            val_b = ctx.get(field_b)

            if isinstance(val_a, (int, float)) and isinstance(val_b, (int, float)):
                values_a.append(val_a)
                values_b.append(val_b)

        if len(values_a) < 5:
            return None

        # Simple correlation coefficient (Pearson-like)
        mean_a = sum(values_a) / len(values_a)
        mean_b = sum(values_b) / len(values_b)

        numerator = sum((a - mean_a) * (b - mean_b) for a, b in zip(values_a, values_b))
        denom_a = sum((a - mean_a) ** 2 for a in values_a) ** 0.5
        denom_b = sum((b - mean_b) ** 2 for b in values_b) ** 0.5

        if denom_a == 0 or denom_b == 0:
            return None

        correlation = numerator / (denom_a * denom_b)

        if abs(correlation) >= threshold:
            pattern_id = f"corr_{self._pattern_counter}"
            self._pattern_counter += 1

            pattern = Pattern(
                pattern_id=pattern_id,
                pattern_type="correlation",
                frequency=len(values_a),
                first_seen=self.action_history[0]["timestamp"],
                last_seen=self.action_history[-1]["timestamp"],
                confidence=abs(correlation),
                metadata={
                    "field_a": field_a,
                    "field_b": field_b,
                    "correlation": correlation,
                    "direction": "positive" if correlation > 0 else "negative",
                },
            )
            self.patterns[pattern_id] = pattern
            return pattern

        return None

    def detect_anomaly(
        self, field: str, std_threshold: float = 2.0
    ) -> List[Tuple[int, float]]:
        """
        Detect anomalous values (outliers) in a field.

        Returns list of (index, z_score) for anomalies.
        """
        values = []
        for entry in self.action_history:
            ctx = entry["context"]
            val = ctx.get(field)
            if isinstance(val, (int, float)):
                values.append(val)

        if len(values) < 10:
            return []

        # Calculate mean and std dev
        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        std_dev = variance**0.5

        if std_dev == 0:
            return []

        # Find anomalies
        anomalies = []
        for i, val in enumerate(values):
            z_score = abs(val - mean) / std_dev
            if z_score > std_threshold:
                anomalies.append((i, z_score))

        return anomalies

    def detect_cyclic_behavior(self, window_size: int = 10) -> Optional[Pattern]:
        """
        Detect cyclic patterns (same state recurring).

        Example: Task execution cycling through same states repeatedly.
        """
        if len(self.action_history) < window_size * 2:
            return None

        # Extract state signatures
        states = []
        for entry in self.action_history:
            # Create state signature from action + key context fields
            action_type = entry["action"].get("action_type", "unknown")
            context_sig = tuple(sorted(entry["context"].keys()))
            states.append((action_type, context_sig))

        # Look for repeating windows
        for period in range(2, window_size + 1):
            for start in range(len(states) - period * 2):
                window_1 = states[start : start + period]
                window_2 = states[start + period : start + period * 2]

                if window_1 == window_2:
                    # Found cyclic pattern
                    pattern_id = f"cycle_{self._pattern_counter}"
                    self._pattern_counter += 1

                    pattern = Pattern(
                        pattern_id=pattern_id,
                        pattern_type="cycle",
                        frequency=2,  # Found at least 2 repetitions
                        first_seen=self.action_history[start]["timestamp"],
                        last_seen=self.action_history[start + period * 2 - 1][
                            "timestamp"
                        ],
                        confidence=0.8,
                        metadata={
                            "period": period,
                            "cycle_states": [s[0] for s in window_1],
                        },
                    )
                    self.patterns[pattern_id] = pattern
                    return pattern

        return None

    def analyze_emergence(self) -> LayerResult:
        """
        Run all pattern detection algorithms and identify emergent behavior.

        Returns LayerResult with detected patterns.
        """
        detected_patterns = []

        # Sequence patterns
        seq_patterns = self.detect_sequence_pattern()
        detected_patterns.extend(seq_patterns)

        # Cyclic behavior
        cycle_pattern = self.detect_cyclic_behavior()
        if cycle_pattern:
            detected_patterns.append(cycle_pattern)

        # Check for emergence events (strong patterns)
        strong_patterns = [p for p in detected_patterns if p.confidence > 0.7]

        if strong_patterns:
            event = EmergenceEvent(
                timestamp=time.time(),
                event_type="pattern_emergence",
                description=f"Detected {len(strong_patterns)} strong emergent patterns",
                patterns_involved=[p.pattern_id for p in strong_patterns],
                strength=sum(p.confidence for p in strong_patterns)
                / len(strong_patterns),
            )
            self.emergence_events.append(event)

            return LayerResult(
                layer="emergence",
                passed=True,
                reason=f"Emergence detected: {len(strong_patterns)} patterns",
                metadata={
                    "patterns_detected": len(detected_patterns),
                    "strong_patterns": len(strong_patterns),
                    "pattern_types": [p.pattern_type for p in detected_patterns],
                    "emergence_strength": event.strength,
                },
                timestamp=time.time(),
            )

        return LayerResult(
            layer="emergence",
            passed=True,
            reason="No significant emergence detected",
            metadata={
                "patterns_detected": len(detected_patterns),
                "history_size": len(self.action_history),
            },
            timestamp=time.time(),
        )

    def evaluate(self, action: Dict[str, Any], context: Dict[str, Any]) -> LayerResult:
        """
        Entry point for pipeline composition.

        Records action and analyzes for emergent patterns.
        """
        # Record action to history
        self.record_action(action, context)

        # Analyze periodically (not every action to save compute)
        if len(self.action_history) % 10 == 0:
            return self.analyze_emergence()

        return LayerResult(
            layer="emergence",
            passed=True,
            reason="Action recorded, awaiting analysis window",
            metadata={"history_size": len(self.action_history)},
            timestamp=time.time(),
        )

    def get_patterns(
        self, pattern_type: Optional[str] = None, min_confidence: float = 0.0
    ) -> List[Pattern]:
        """Query detected patterns."""
        patterns = list(self.patterns.values())

        if pattern_type:
            patterns = [p for p in patterns if p.pattern_type == pattern_type]

        if min_confidence > 0:
            patterns = [p for p in patterns if p.confidence >= min_confidence]

        return patterns


# Module-level instance
_emergence = EmergenceLayer()


def record_action(action: Dict[str, Any], context: Dict[str, Any]):
    """Record action to global instance."""
    _emergence.record_action(action, context)


def analyze_emergence() -> LayerResult:
    """Analyze patterns using global instance."""
    return _emergence.analyze_emergence()


def evaluate(action: Dict[str, Any], context: Dict[str, Any]) -> LayerResult:
    """Standalone evaluation."""
    return _emergence.evaluate(action, context)


def get_patterns(
    pattern_type: Optional[str] = None, min_confidence: float = 0.0
) -> List[Pattern]:
    """Get patterns from global instance."""
    return _emergence.get_patterns(pattern_type, min_confidence)
